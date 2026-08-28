import { describe, expect, it } from "vitest";

import { createIpcClient } from "../../src/ipc/client";
import { IDEMPOTENCY_KEY_HEADER, TOKEN_HEADER } from "../../src/ipc/endpoints";
import { loadSettings, persistModsPath, persistTelemetryEnabled } from "../../src/settings/settings";
import { makeSettingsSidecar } from "../fixtures/mock-settings";
import type { FetchCall } from "../fixtures/mock-sse";

const BASE = "http://127.0.0.1:5599";
const TOKEN = "tok-settings-1";

const methodOf = (c: FetchCall): string => (c.init?.method ?? "GET").toUpperCase();

describe("Settings persistence over the FULL-REPLACE PUT /settings contract (§4)", () => {
  it("test_load_settings_round_trips — spec(§4)", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: "/m/Mods", telemetryEnabled: false });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    const settings = await loadSettings(client);
    expect(settings.simsModsPath).toBe("/m/Mods");
    expect(settings.telemetryEnabled).toBe(false);
  });

  it("test_persist_mods_path_read_modify_writes_full_object — spec(§4)", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: null, telemetryEnabled: true });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    const updated = await persistModsPath(client, "/m/Mods");
    expect(updated.simsModsPath).toBe("/m/Mods");
    expect(updated.telemetryEnabled).toBe(true); // sibling preserved via read-modify-write

    // A GET (read) precedes the PUT (write) — read-modify-write, not a blind partial PUT.
    const methods = sidecar.calls.map(methodOf);
    expect(methods.indexOf("GET")).toBeGreaterThanOrEqual(0);
    expect(methods.indexOf("GET")).toBeLessThan(methods.indexOf("PUT"));

    // The PUT body is the FULL object — BOTH fields present (full-replace contract).
    const put = sidecar.calls.find((c) => methodOf(c) === "PUT");
    expect(put).toBeDefined();
    const body = JSON.parse(String(put?.init?.body ?? "{}")) as Record<string, unknown>;
    expect(Object.keys(body).sort()).toEqual(["simsModsPath", "telemetryEnabled"]);
    expect(body.telemetryEnabled).toBe(true);

    // Reread: under full-replace, telemetry survived ONLY because of the read-modify-write.
    const reread = await loadSettings(client);
    expect(reread.simsModsPath).toBe("/m/Mods");
    expect(reread.telemetryEnabled).toBe(true);
  });

  it("test_persist_telemetry_read_modify_writes_full_object — spec(§4)", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: "/m/Mods", telemetryEnabled: true });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    const updated = await persistTelemetryEnabled(client, false);
    expect(updated.telemetryEnabled).toBe(false);
    expect(updated.simsModsPath).toBe("/m/Mods"); // sibling preserved via read-modify-write

    const methods = sidecar.calls.map(methodOf);
    expect(methods.indexOf("GET")).toBeGreaterThanOrEqual(0);
    expect(methods.indexOf("GET")).toBeLessThan(methods.indexOf("PUT")); // GET precedes PUT

    const put = sidecar.calls.find((c) => methodOf(c) === "PUT");
    expect(put).toBeDefined();
    const body = JSON.parse(String(put?.init?.body ?? "{}")) as Record<string, unknown>;
    expect(Object.keys(body).sort()).toEqual(["simsModsPath", "telemetryEnabled"]);
    expect(body.simsModsPath).toBe("/m/Mods");

    const reread = await loadSettings(client);
    expect(reread.simsModsPath).toBe("/m/Mods");
    expect(reread.telemetryEnabled).toBe(false);
  });

  it("test_mock_full_replace_resets_omitted_field — spec(§4)", async () => {
    // A direct PARTIAL PUT against the mock must RESET the omitted field to its default — proving
    // the mock models full-replace and would CATCH a partial-PUT regression (not mask it).
    const sidecar = makeSettingsSidecar({ simsModsPath: "/m/Mods", telemetryEnabled: true });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    await client.updateSettings({ telemetryEnabled: false }); // omits simsModsPath

    const reread = await loadSettings(client);
    expect(reread.simsModsPath).toBeNull(); // reset to default under full-replace
    expect(reread.telemetryEnabled).toBe(false);
  });

  it("test_settings_write_never_carries_a_secret — safety rule 5", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: null, telemetryEnabled: false });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    await persistTelemetryEnabled(client, true);

    const put = sidecar.calls.find((c) => methodOf(c) === "PUT");
    expect(put).toBeDefined();
    const body = JSON.parse(String(put?.init?.body ?? "{}")) as Record<string, unknown>;
    expect(Object.keys(body).length).toBeGreaterThan(0); // non-vacuous scan
    for (const key of Object.keys(body)) {
      expect(["simsModsPath", "telemetryEnabled"]).toContain(key);
      expect(key).not.toMatch(/key|secret|token|password|credential/i);
    }
  });

  it("test_settings_get_omits_idempotency_put_carries_both — spec(§4) R9", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: null, telemetryEnabled: false });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    await persistModsPath(client, "/x/Mods");

    const get = sidecar.calls.find((c) => methodOf(c) === "GET");
    const put = sidecar.calls.find((c) => methodOf(c) === "PUT");
    expect(get).toBeDefined();
    expect(put).toBeDefined();

    // The conflated SETTINGS endpoint ∈ MUTATING, but its GET read omits Idempotency-Key while
    // still carrying the token; the PUT write carries both.
    const getHeaders = new Headers(get?.init?.headers);
    expect(getHeaders.get(TOKEN_HEADER)).toBe(TOKEN);
    expect(getHeaders.get(IDEMPOTENCY_KEY_HEADER)).toBeNull();

    const putHeaders = new Headers(put?.init?.headers);
    expect(putHeaders.get(TOKEN_HEADER)).toBe(TOKEN);
    expect(putHeaders.get(IDEMPOTENCY_KEY_HEADER)).toBeTruthy();
  });
});

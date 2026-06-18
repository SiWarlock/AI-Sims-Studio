import { describe, expect, it } from "vitest";

import { createIpcClient } from "../../src/ipc/client";
import { IDEMPOTENCY_KEY_HEADER, TOKEN_HEADER } from "../../src/ipc/endpoints";
import { loadSettings, persistModsPath } from "../../src/settings/settings";
import { makeSettingsSidecar } from "../fixtures/mock-settings";

const BASE = "http://127.0.0.1:5599";
const TOKEN = "tok-settings-1";

describe("Settings persistence over the frozen GET/PUT /settings contract (§4)", () => {
  it("test_load_settings_round_trips — spec(§4)", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: "/m/Mods", telemetryEnabled: false });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    const settings = await loadSettings(client);
    expect(settings.simsModsPath).toBe("/m/Mods");
    expect(settings.telemetryEnabled).toBe(false);
  });

  it("test_persist_mods_path_puts_and_round_trips — spec(§4) fp-3", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: null, telemetryEnabled: false });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    const updated = await persistModsPath(client, "/new/The Sims 4/Mods");
    expect(updated.simsModsPath).toBe("/new/The Sims 4/Mods");

    // Round-trip: a subsequent read returns the persisted value.
    const reread = await loadSettings(client);
    expect(reread.simsModsPath).toBe("/new/The Sims 4/Mods");

    // fp-3: the PUT carried the per-launch token.
    const put = sidecar.calls.find((c) => (c.init?.method ?? "GET").toUpperCase() === "PUT");
    expect(put).toBeDefined();
    expect(new Headers(put?.init?.headers).get(TOKEN_HEADER)).toBe(TOKEN);
  });

  it("test_settings_write_never_carries_a_secret — safety rule 5", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: null, telemetryEnabled: false });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    await persistModsPath(client, "/some/Mods");

    const put = sidecar.calls.find((c) => (c.init?.method ?? "GET").toUpperCase() === "PUT");
    const body = JSON.parse(String(put?.init?.body ?? "{}")) as Record<string, unknown>;
    // Only the two protocol-level settings fields may ride the body — never a secret.
    for (const key of Object.keys(body)) {
      expect(["simsModsPath", "telemetryEnabled"]).toContain(key);
      expect(key).not.toMatch(/key|secret|token|password|credential/i);
    }
  });

  it("test_settings_get_omits_idempotency_put_carries_both — spec(§4) R9", async () => {
    const sidecar = makeSettingsSidecar({ simsModsPath: null, telemetryEnabled: false });
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: sidecar.fetchImpl });

    await loadSettings(client);
    await persistModsPath(client, "/x/Mods");

    const get = sidecar.calls.find((c) => (c.init?.method ?? "GET").toUpperCase() === "GET");
    const put = sidecar.calls.find((c) => (c.init?.method ?? "GET").toUpperCase() === "PUT");

    // The conflated SETTINGS endpoint ∈ MUTATING, but its GET read omits Idempotency-Key
    // (ipc.py: "its GET simply omits the optional key") while still carrying the token.
    const getHeaders = new Headers(get?.init?.headers);
    expect(getHeaders.get(TOKEN_HEADER)).toBe(TOKEN);
    expect(getHeaders.get(IDEMPOTENCY_KEY_HEADER)).toBeNull();

    // The PUT write carries both the token and an Idempotency-Key.
    const putHeaders = new Headers(put?.init?.headers);
    expect(putHeaders.get(TOKEN_HEADER)).toBe(TOKEN);
    expect(putHeaders.get(IDEMPOTENCY_KEY_HEADER)).toBeTruthy();
  });
});

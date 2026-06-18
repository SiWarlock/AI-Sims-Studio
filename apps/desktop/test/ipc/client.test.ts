import { describe, expect, it, vi } from "vitest";

import { buildRequestHeaders, createIpcClient } from "../../src/ipc/client";
import {
  ENDPOINTS,
  IDEMPOTENCY_KEY_HEADER,
  TOKEN_HEADER,
  isMutating,
  type EndpointId,
} from "../../src/ipc/endpoints";
import { subscribeEvents } from "../../src/ipc/sse";
import {
  eventStreamResponse,
  jsonResponse,
  recordingFetch,
  sseFrame,
  streamFromChunks,
} from "../fixtures/mock-sse";

const BASE = "http://127.0.0.1:5599";
const TOKEN = "tok-secret-abc123";

describe("IPC client — token + idempotency boundary (§4/§16)", () => {
  it("test_client_attaches_token_on_every_request — spec(§4) §16 forbidden-pattern-3", async () => {
    const rf = recordingFetch([
      jsonResponse({ run: { id: "r1", projectId: "p1", runType: "full", status: "running" } }),
      jsonResponse({ items: [], total: 0 }),
    ]);
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: rf.fetchImpl });

    await client.startRun("p1");
    await client.listProjects();

    expect(rf.calls.length).toBe(2);
    expect(rf.headerOf(0, TOKEN_HEADER)).toBe(TOKEN);
    expect(rf.headerOf(1, TOKEN_HEADER)).toBe(TOKEN);
  });

  it("test_client_without_token_throws — spec(§4) forbidden-pattern-3 (no untokened client)", () => {
    expect(() => createIpcClient({ baseUrl: BASE, token: "" })).toThrow();
    expect(() =>
      createIpcClient({ baseUrl: BASE, token: undefined as unknown as string }),
    ).toThrow();
  });

  it("test_client_idempotency_key_on_mutating_only — spec(§4) R9", () => {
    const ids = Object.keys(ENDPOINTS) as EndpointId[];
    expect(ids.length).toBe(15);
    for (const id of ids) {
      const headers = buildRequestHeaders({ endpointId: id, token: TOKEN });
      if (isMutating(id)) {
        expect(headers[IDEMPOTENCY_KEY_HEADER], `${id} should carry idempotency key`).toBeDefined();
      } else {
        expect(headers[IDEMPOTENCY_KEY_HEADER], `${id} must omit idempotency key`).toBeUndefined();
      }
      expect(headers[TOKEN_HEADER]).toBe(TOKEN);
    }
    // The one read-only endpoint, explicitly.
    expect(
      buildRequestHeaders({ endpointId: "GET /projects", token: TOKEN })[IDEMPOTENCY_KEY_HEADER],
    ).toBeUndefined();
  });

  it("test_get_readiness_is_token_bearing_read_only — spec(§4) Lesson 5", async () => {
    const rf = recordingFetch([jsonResponse({ overall: "ready", checks: [] })]);
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: rf.fetchImpl });

    await client.getReadiness();

    expect(rf.calls.length).toBe(1);
    expect(rf.calls[0]?.init?.method).toBe("GET");
    expect(rf.calls[0]?.url).toContain("/readiness");
    expect(rf.headerOf(0, TOKEN_HEADER)).toBe(TOKEN);
    // read-only ⇒ no idempotency key. headerOf goes through Headers.get(), which returns null
    // (not undefined) for an absent header — hence toBeNull here vs toBeUndefined on plain dicts.
    expect(rf.headerOf(0, IDEMPOTENCY_KEY_HEADER)).toBeNull();
  });

  it("test_get_readiness_returns_parsed_report — spec(§4)", async () => {
    const rf = recordingFetch([
      jsonResponse({
        overall: "blocked",
        checks: [{ subsystem: "blender", status: "blocked", remediation: "Install Blender 5.1" }],
      }),
    ]);
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: rf.fetchImpl });

    const report = await client.getReadiness();

    expect(report.overall).toBe("blocked");
    expect(report.checks).toHaveLength(1);
    expect(report.checks[0]?.subsystem).toBe("blender");
  });

  it("test_test_provider_is_mutating_post_with_idempotency_key — spec(§4) Lesson 5", async () => {
    const rf = recordingFetch([jsonResponse({ ok: true, latencyMs: 12 })]);
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: rf.fetchImpl });

    await client.testProvider("openai");

    expect(rf.calls[0]?.init?.method).toBe("POST");
    expect(rf.calls[0]?.url).toContain("/settings/providers/openai/test");
    expect(rf.headerOf(0, TOKEN_HEADER)).toBe(TOKEN);
    expect(rf.headerOf(0, IDEMPOTENCY_KEY_HEADER)).not.toBeNull(); // mutating ⇒ idempotency key
  });

  it("test_test_provider_no_secret_in_body — rule-5 (keychain-only, never on the wire)", async () => {
    const rf = recordingFetch([jsonResponse({ ok: true }), jsonResponse({ ok: true })]);
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: rf.fetchImpl });

    await client.testProvider("openai", { model: "gpt-4" });
    const body = JSON.parse(String(rf.calls[0]?.init?.body ?? "{}")) as Record<string, unknown>;
    expect(body).toEqual({ model: "gpt-4" }); // ONLY model rides the body
    expect(body).not.toHaveProperty("apiKey");
    expect(body).not.toHaveProperty("key");
    expect(body).not.toHaveProperty("secret");

    await client.testProvider("openai"); // no body arg ⇒ no request body at all
    expect(rf.calls[1]?.init?.body).toBeUndefined();
  });

  it("test_test_provider_returns_parsed_response — spec(§4)", async () => {
    const rf = recordingFetch([
      jsonResponse({
        ok: false,
        error: {
          category: "provider",
          code: "PROVIDER_AUTH_QUOTA",
          creatorMessage: "bad key",
          maintainerDetail: "x",
          retryable: false,
        },
      }),
    ]);
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: rf.fetchImpl });

    const resp = await client.testProvider("openai");

    expect(resp.ok).toBe(false);
    expect(resp.error?.code).toBe("PROVIDER_AUTH_QUOTA");
  });

  it("test_token_never_logged_or_in_url — spec(§4) §16 forbidden-pattern-3", async () => {
    const spies = (["log", "info", "warn", "error", "debug"] as const).map((m) =>
      vi.spyOn(console, m).mockImplementation(() => undefined),
    );
    const rf = recordingFetch([
      jsonResponse({ run: { id: "r1", projectId: "p1", runType: "full", status: "running" } }),
      jsonResponse({ items: [], total: 0 }),
      eventStreamResponse(
        streamFromChunks([
          sseFrame({ event: "progress", id: "1", runId: "r1", fraction: 0.1 }),
        ]),
      ),
    ]);
    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl: rf.fetchImpl });

    await client.startRun("p1");
    await client.listProjects();
    await subscribeEvents({
      baseUrl: BASE,
      projectId: "p1",
      token: TOKEN,
      fetchImpl: rf.fetchImpl,
      maxReconnects: 0,
      onEvent: () => undefined,
    });

    for (const call of rf.calls) {
      expect(call.url).not.toContain(TOKEN);
    }
    for (const spy of spies) {
      for (const callArgs of spy.mock.calls) {
        expect(JSON.stringify(callArgs)).not.toContain(TOKEN);
      }
      spy.mockRestore();
    }
  });
});

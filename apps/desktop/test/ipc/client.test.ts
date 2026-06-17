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
    expect(ids.length).toBe(14);
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

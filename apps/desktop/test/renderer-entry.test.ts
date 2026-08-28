import { describe, expect, it } from "vitest";

import { startRenderer } from "../src/renderer-entry";
import {
  eventStreamResponse,
  jsonResponse,
  sseFrame,
  streamFromChunks,
} from "./fixtures/mock-sse";

const BASE = "http://127.0.0.1:5599";

/**
 * Regression (RED #8): the 7.1 SSE observer must still boot from the renderer entry that main.tsx
 * (the React root) invokes. startRenderer wires the IPC client + SSE subscription + projection; the
 * React migration must not break that path.
 */
describe("renderer entry — observer still boots under the React root (no 7.1 regression)", () => {
  it("test_observer_still_boots_under_react_root — spec(§3)", async () => {
    const fetchImpl = (async (input: Parameters<typeof fetch>[0]) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/events")) {
        return eventStreamResponse(
          streamFromChunks([
            sseFrame({ event: "progress", id: "1", runId: "r1", fraction: 0.5 }),
            sseFrame({ event: "done", id: "2", runId: "r1", status: "succeeded" }),
          ]),
        );
      }
      return jsonResponse({});
    }) as typeof fetch;

    const handle = startRenderer({
      token: "tok-react",
      baseUrl: BASE,
      projectId: "p1",
      fetchImpl,
      maxReconnects: 0,
    });
    await handle.done;

    const state = handle.getState();
    expect(state.lastEventId).toBe("2");
    expect((state.runs.r1 as { status?: string }).status).toBe("succeeded");
  });
});

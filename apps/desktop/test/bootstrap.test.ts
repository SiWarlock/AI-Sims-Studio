import { describe, expect, it } from "vitest";

import { bootstrapObserver } from "../src/bootstrap";
import {
  eventStreamResponse,
  jsonResponse,
  sseFrame,
  streamFromChunks,
} from "./fixtures/mock-sse";

const BASE = "http://127.0.0.1:5599";

/**
 * PROPOSED ADD (Step-2.5): pins the renderer-entry wiring contract — bootstrapObserver constructs
 * client + SSE + projection and the projection reflects the streamed events. Backs the Step-7.5
 * reachability claim (`/wired bootstrapObserver`) with an executable assertion.
 */
describe("bootstrapObserver — renderer entry wiring (§3)", () => {
  it("test_bootstrap_feeds_sse_into_projection — spec(§3)", async () => {
    const fetchImpl = (async (input: Parameters<typeof fetch>[0]) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/events")) {
        return eventStreamResponse(
          streamFromChunks([
            sseFrame({ event: "progress", id: "1", runId: "r1", fraction: 0.25 }),
            sseFrame({ event: "done", id: "2", runId: "r1", status: "succeeded" }),
          ]),
        );
      }
      return jsonResponse({});
    }) as typeof fetch;

    const handle = bootstrapObserver("tok-bootstrap", BASE, {
      projectId: "p1",
      fetchImpl,
      maxReconnects: 0,
    });
    await handle.done;

    const state = handle.getState();
    expect(state.lastEventId).toBe("2");
    expect(state.runs.r1).toBeDefined();
    expect((state.runs.r1 as { status?: string }).status).toBe("succeeded");
  });
});

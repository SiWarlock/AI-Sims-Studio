import { describe, expect, it } from "vitest";

import { TOKEN_HEADER } from "../../src/ipc/endpoints";
import { subscribeEvents } from "../../src/ipc/sse";
import {
  commentFrame,
  eventStreamResponse,
  recordingFetch,
  sseFrame,
  streamFromChunks,
} from "../fixtures/mock-sse";

const BASE = "http://127.0.0.1:5599";
const TOKEN = "tok-1";

describe("SSE reader — Last-Event-ID reconnect-replay (§3)", () => {
  it("test_sse_reconnect_sends_last_event_id_and_drops_replayed — spec(§3)", async () => {
    const stream1 = eventStreamResponse(
      streamFromChunks([
        sseFrame({ event: "progress", id: "1", runId: "r1", fraction: 0.1 }),
        commentFrame(), // heartbeat — must not surface as an event
        sseFrame({ event: "progress", id: "2", runId: "r1", fraction: 0.2 }),
        sseFrame({ event: "step-state", id: "3", runId: "r1", stepId: "s1", status: "running" }),
      ]),
    );
    // The server replays from Last-Event-ID inclusively (ids 2,3) then continues with 4.
    const stream2 = eventStreamResponse(
      streamFromChunks([
        sseFrame({ event: "progress", id: "2", runId: "r1", fraction: 0.2 }),
        sseFrame({ event: "step-state", id: "3", runId: "r1", stepId: "s1", status: "running" }),
        sseFrame({ event: "done", id: "4", runId: "r1", status: "succeeded" }),
      ]),
    );
    const rf = recordingFetch([stream1, stream2]);

    const seen: string[] = [];
    await subscribeEvents({
      baseUrl: BASE,
      projectId: "p1",
      token: TOKEN,
      fetchImpl: rf.fetchImpl,
      maxReconnects: 1,
      onEvent: (e) => seen.push(e.id),
    });

    // Each id delivered exactly once; the replayed 2,3 are dropped (id ≤ cursor).
    expect(seen).toEqual(["1", "2", "3", "4"]);
    // The reconnect (second fetch) presented the cursor.
    expect(rf.headerOf(1, "Last-Event-ID")).toBe("3");
    expect(rf.calls.length).toBe(2);
    // Directed assertion (§4/§16/fp-3): the token rides the SSE GET on BOTH the initial open
    // AND the reconnect — the token-on-every-request invariant must survive a reconnect.
    expect(rf.headerOf(0, TOKEN_HEADER)).toBe(TOKEN);
    expect(rf.headerOf(1, TOKEN_HEADER)).toBe(TOKEN);
  });

  it("test_sse_delivers_frame_split_across_chunks — spec(§3) buffer stitching", async () => {
    const frame = sseFrame({ event: "progress", id: "1", runId: "r1", fraction: 0.5 });
    const mid = Math.floor(frame.length / 2);
    const rf = recordingFetch([
      eventStreamResponse(streamFromChunks([frame.slice(0, mid), frame.slice(mid)])),
    ]);
    const seen: string[] = [];
    await subscribeEvents({
      baseUrl: BASE,
      projectId: "p1",
      token: TOKEN,
      fetchImpl: rf.fetchImpl,
      maxReconnects: 0,
      onEvent: (e) => seen.push(e.id),
    });
    expect(seen).toEqual(["1"]); // a frame split across two reads is reassembled and delivered once
  });

  it("test_sse_idle_reconnect_backs_off — review hardening (no hot-spin)", async () => {
    // Two immediately-empty streams ⇒ one reconnect that delivered nothing ⇒ one backoff sleep.
    const rf = recordingFetch([
      eventStreamResponse(streamFromChunks([])),
      eventStreamResponse(streamFromChunks([])),
    ]);
    const sleeps: number[] = [];
    await subscribeEvents({
      baseUrl: BASE,
      projectId: "p1",
      token: TOKEN,
      fetchImpl: rf.fetchImpl,
      maxReconnects: 1,
      onEvent: () => undefined,
      sleepImpl: (ms) => {
        sleeps.push(ms);
        return Promise.resolve();
      },
    });
    expect(sleeps).toHaveLength(1);
    expect(sleeps[0]).toBeGreaterThan(0);
  });
});

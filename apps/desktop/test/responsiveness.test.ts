import { describe, expect, it } from "vitest";

import { createIpcClient } from "../src/ipc/client";
import { subscribeEvents } from "../src/ipc/sse";
import type { SseEvent } from "../src/ipc/sse-schema";
import {
  commentFrame,
  controllableStream,
  eventStreamResponse,
  jsonResponse,
  sseFrame,
} from "./fixtures/mock-sse";

const BASE = "http://127.0.0.1:5599";
const TOKEN = "tok-21";

async function waitFor(predicate: () => boolean, label = "condition"): Promise<void> {
  for (let i = 0; i < 200; i++) {
    if (predicate()) return;
    await new Promise((r) => setTimeout(r, 0));
  }
  throw new Error(`waitFor timed out: ${label}`);
}

describe("§21 UI-responsiveness gate — slow stage must not block ack/heartbeat", () => {
  it("test_ui_responsiveness_slow_stage_does_not_block — spec(§21)", async () => {
    const ctrl = controllableStream();
    // Route by endpoint: the events stream is the long-lived SSE; everything else is an ack body.
    const fetchImpl = (async (input: Parameters<typeof fetch>[0]) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.endsWith("/events")) return eventStreamResponse(ctrl.stream);
      return jsonResponse({
        run: { id: "r1", projectId: "p1", runType: "full", status: "running" },
      });
    }) as typeof fetch;

    const client = createIpcClient({ baseUrl: BASE, token: TOKEN, fetchImpl });
    const seen: SseEvent[] = [];
    const sub = subscribeEvents({
      baseUrl: BASE,
      projectId: "p1",
      token: TOKEN,
      fetchImpl,
      maxReconnects: 0,
      onEvent: (e) => seen.push(e),
    });

    // A slow stage begins (running) and stays pending — its terminal event is withheld.
    ctrl.push(sseFrame({ event: "step-state", id: "1", runId: "r1", stepId: "slow", status: "running" }));
    await waitFor(() => seen.some((e) => e.id === "1"), "slow stage running observed");

    // Command-ack resolves promptly — NOT blocked by the still-pending slow stage.
    const ack = await client.startRun("p1");
    expect(ack.run.id).toBe("r1");
    expect(seen.some((e) => e.event === "done")).toBe(false); // slow stage not finished

    // Heartbeat + unrelated progress keep arriving while the slow stage is pending.
    ctrl.push(commentFrame());
    ctrl.push(sseFrame({ event: "progress", id: "2", runId: "r1", fraction: 0.4 }));
    ctrl.push(sseFrame({ event: "progress", id: "3", runId: "r1", fraction: 0.6 }));
    await waitFor(
      () => seen.filter((e) => e.event === "progress").length >= 2,
      "progress keeps flowing under a pending slow stage",
    );
    expect(seen.some((e) => e.event === "done")).toBe(false);

    // Finally the slow stage completes; the stream drains cleanly.
    ctrl.push(sseFrame({ event: "done", id: "4", runId: "r1", status: "succeeded" }));
    ctrl.close();
    await sub;
    expect(seen.some((e) => e.id === "4")).toBe(true);
  });
});

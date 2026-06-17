import { describe, expect, it } from "vitest";

import { parseSseEvent } from "../../src/ipc/sse-schema";
import { initialState, projectEvent } from "../../src/state/projection";

const STREAM = [
  { event: "progress", id: "1", runId: "r1", fraction: 0.3 },
  { event: "cost", id: "2", runId: "r1", amountCents: 100, currency: "USD" },
  { event: "step-state", id: "3", runId: "r1", stepId: "s1", status: "running" },
  { event: "done", id: "4", runId: "r1", status: "succeeded" },
].map((raw) => parseSseEvent(raw));

function replay(events: ReturnType<typeof parseSseEvent>[]) {
  return events.reduce((s, e) => projectEvent(s, e), initialState());
}

describe("Observer projection — pure idempotent reducer (§3, forbidden-pattern-2)", () => {
  it("test_projection_is_pure_and_idempotent — spec(§3)", () => {
    const live = replay(STREAM);

    // Pure: applying an event does not mutate its input state.
    const before = initialState();
    const beforeSnapshot = JSON.stringify(before);
    const after = projectEvent(before, STREAM[1]);
    expect(JSON.stringify(before)).toBe(beforeSnapshot);
    expect(after).not.toBe(before);

    // Idempotent: re-applying an already-seen event id is a no-op (cost not double-counted).
    const reapplied = projectEvent(live, STREAM[1]);
    expect(reapplied).toEqual(live);
    expect((reapplied.runs.r1 as { costCents: number }).costCents).toBe(100);

    // Replaying the whole stream reproduces the same read-model.
    expect(replay(STREAM)).toEqual(live);
  });

  it("test_projection_holds_no_durable_authority — spec(§3) forbidden-pattern-2", () => {
    const live = replay(STREAM);
    // A fresh projection rebuilt solely from a replayed stream equals the live state —
    // the read-model carries no authority beyond the stream it is derived from.
    const rebuilt = replay(STREAM);
    expect(rebuilt).toEqual(live);

    // Out-of-order replay of already-seen ids does not corrupt the read-model.
    const withReplay = [...STREAM, STREAM[0], STREAM[1]].reduce(
      (s, e) => projectEvent(s, e),
      initialState(),
    );
    expect(withReplay).toEqual(live);
  });
});

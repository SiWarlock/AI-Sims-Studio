import { describe, expect, it } from "vitest";

import { SSE_EVENT_TAGS, parseSseEvent } from "../../src/ipc/sse-schema";

const VALID: Record<string, Record<string, unknown>> = {
  progress: { event: "progress", id: "1", runId: "r1", fraction: 0.5, message: "halfway" },
  "step-state": { event: "step-state", id: "2", runId: "r1", stepId: "s1", status: "running" },
  log: { event: "log", id: "3", level: "info", message: "hello", stepId: null },
  validation: { event: "validation", id: "4", scope: "item", severity: "warn", message: "m" },
  cost: { event: "cost", id: "5", runId: "r1", amountCents: 120, currency: "USD" },
  "gate-needed": { event: "gate-needed", id: "6", runId: "r1", gate: "plan", itemId: "i1" },
  done: { event: "done", id: "7", runId: "r1", status: "succeeded" },
  error: {
    event: "error",
    id: "8",
    error: {
      category: "system",
      code: "SYSTEM",
      creatorMessage: "Something broke",
      maintainerDetail: "stack",
      retryable: false,
    },
    runId: "r1",
    stepId: null,
  },
};

describe("SSE Zod boundary — frozen §4 taxonomy (§4)", () => {
  it("test_sse_parses_each_event_tag — spec(§4) D15 domain-enum tightening", () => {
    for (const tag of SSE_EVENT_TAGS) {
      const parsed = parseSseEvent(VALID[tag]) as Record<string, unknown>;
      expect(parsed.event).toBe(tag);
    }
    // Domain-enum fields survive intact (D15-tightened).
    const step = parseSseEvent(VALID["step-state"]) as { status: string };
    expect(step.status).toBe("running");
    const val = parseSseEvent(VALID.validation) as { scope: string; severity: string };
    expect(val.scope).toBe("item");
    expect(val.severity).toBe("warn");
    const gate = parseSseEvent(VALID["gate-needed"]) as { gate: string };
    expect(gate.gate).toBe("plan");
  });

  it("test_sse_rejects_unknown_tag_and_malformed — spec(§4) extra=forbid boundary", () => {
    // Unknown event tag.
    expect(() => parseSseEvent({ event: "bogus", id: "x" })).toThrow();
    // Missing a required field (progress.fraction).
    expect(() => parseSseEvent({ event: "progress", id: "x", runId: "r1" })).toThrow();
    // Out-of-enum domain value (step-state.status).
    expect(() =>
      parseSseEvent({ event: "step-state", id: "x", runId: "r1", stepId: "s1", status: "boom" }),
    ).toThrow();
    // Extra/unknown field is rejected (strict boundary).
    expect(() =>
      parseSseEvent({ event: "progress", id: "x", runId: "r1", fraction: 0.2, sneaky: true }),
    ).toThrow();
  });

  it("test_sse_error_event_code_tolerance — carry-forward 0.2/D10b (parseErrorCode→SYSTEM)", () => {
    const unknown = parseSseEvent({
      ...VALID.error,
      error: { ...(VALID.error.error as object), code: "FUTURE_CODE_NOT_YET_KNOWN" },
    }) as { error: { code: string } };
    expect(unknown.error.code).toBe("SYSTEM");

    const known = parseSseEvent({
      ...VALID.error,
      error: { ...(VALID.error.error as object), code: "PROVIDER_TIMEOUT" },
    }) as { error: { code: string } };
    expect(known.error.code).toBe("PROVIDER_TIMEOUT");
  });

  it("test_sse_schema_type_parity_with_generated — root CLAUDE.md import-the-generated-type", () => {
    // Runtime half of the parity guard: every generated SSE member tag has a Zod branch.
    // (The compile-time half — z.infer ≡ the generated union members + domain enums — lives as
    //  static assertions in sse-schema.ts and is enforced by `pnpm typecheck` at Step 8.)
    expect([...SSE_EVENT_TAGS].sort()).toEqual(
      [
        "cost",
        "done",
        "error",
        "gate-needed",
        "log",
        "progress",
        "step-state",
        "validation",
      ].sort(),
    );
  });
});

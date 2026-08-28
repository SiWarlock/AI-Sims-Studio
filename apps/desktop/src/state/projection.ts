/**
 * Server-driven state projection (§3). A pure, idempotent reducer over the SSE event stream — the
 * read-model holds NO durable pipeline authority (forbidden pattern 2): the sidecar is the source
 * of truth, and this state is fully rebuildable by replaying the stream. Re-applying an already-
 * seen event id is a no-op, so an inclusive `Last-Event-ID` replay never double-counts (e.g. cost).
 */
import type { SseEvent } from "../ipc/sse-schema";

export interface RunView {
  costCents: number;
  fraction?: number;
  status?: string;
}

export interface PendingGate {
  gate: string;
  runId: string;
  itemId: string | null;
}

export interface ObserverState {
  lastEventId: string | null;
  seenEventIds: ReadonlySet<string>;
  runs: Record<string, RunView>;
  steps: Record<string, string>;
  pendingGate: PendingGate | null;
}

export function initialState(): ObserverState {
  return {
    lastEventId: null,
    seenEventIds: new Set<string>(),
    runs: {},
    steps: {},
    pendingGate: null,
  };
}

export function projectEvent(state: ObserverState, event: SseEvent): ObserverState {
  if (state.seenEventIds.has(event.id)) return state; // idempotent: a seen id is a no-op

  const seenEventIds = new Set(state.seenEventIds);
  seenEventIds.add(event.id);
  const runs: Record<string, RunView> = { ...state.runs };
  const steps: Record<string, string> = { ...state.steps };
  let pendingGate = state.pendingGate;

  const patchRun = (runId: string, patch: Partial<RunView>): void => {
    const prev = runs[runId] ?? { costCents: 0 };
    runs[runId] = { ...prev, ...patch };
  };

  switch (event.event) {
    case "progress":
      patchRun(event.runId, { fraction: event.fraction });
      break;
    case "step-state":
      steps[event.stepId] = event.status;
      break;
    case "cost": {
      const prev = runs[event.runId] ?? { costCents: 0 };
      runs[event.runId] = { ...prev, costCents: prev.costCents + event.amountCents };
      break;
    }
    case "gate-needed":
      pendingGate = { gate: event.gate, runId: event.runId, itemId: event.itemId ?? null };
      break;
    case "done":
      patchRun(event.runId, { status: event.status });
      break;
    case "log":
    case "validation":
    case "error":
      // Cursor/seen advance only for now; the read-model surfaces these in 7.3.
      break;
  }

  return { lastEventId: event.id, seenEventIds, runs, steps, pendingGate };
}

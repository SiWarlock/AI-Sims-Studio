/**
 * §18(4) system-readiness gate. A pure decision over the server-driven `GET /readiness`
 * ReadinessReport: whether "New Project" may start. The gate computes its OWN safety decision from
 * per-subsystem `check.status` (fail-safe allow-list) — `report.overall` is advisory/display only.
 *
 * Precedence: blocked > indeterminate (empty checks / off-contract status) > ready. A known,
 * actionable subsystem blockage is never masked behind "indeterminate", and an unrecognized status
 * fails CLOSED rather than starting optimistically. The visual gate screen (button-disable +
 * remediation list) is a thin consumer that rides design-fixture review (D4), not this module.
 */
import type {
  ReadinessCheck,
  ReadinessReport,
} from "../../../../packages/contracts/generated/contracts";
import type { IpcClient } from "../ipc/client";

export type ReadinessGateState = "ready" | "blocked" | "indeterminate";

export interface ReadinessGate {
  state: ReadinessGateState;
  canStartNewProject: boolean;
  /** Every blocking check (not just the first) — the per-subsystem remediation surface. */
  blocking: ReadinessCheck[];
  /** Impaired-not-missing checks — surfaced as a non-blocking warning. */
  degraded: ReadinessCheck[];
}

/**
 * Pure gate decision. New Project may start ONLY when every check is a recognized non-blocking
 * state ({ready, degraded}) — a fail-safe allow-list, so an off-contract/garbage status fails
 * closed. Any `blocked` check ⇒ blocked (takes precedence); empty checks ⇒ indeterminate. Derived
 * from per-check status, never `report.overall`.
 */
export function computeReadinessGate(report: ReadinessReport): ReadinessGate {
  const { checks } = report;
  const blocking = checks.filter((c) => c.status === "blocked");
  const degraded = checks.filter((c) => c.status === "degraded");

  if (checks.length === 0) {
    return { state: "indeterminate", canStartNewProject: false, blocking: [], degraded: [] };
  }
  // blocked > indeterminate: a real blockage is surfaced even if another status is unrecognized.
  if (blocking.length > 0) {
    return { state: "blocked", canStartNewProject: false, blocking, degraded };
  }
  // Allow-list: every check must be a recognized non-blocking state; else fail closed.
  // An off-contract status yields "indeterminate" — we reached no conclusion, so (like the
  // empty-checks path) surface no partial warning: blocking AND degraded are both empty.
  const allRecognizedNonBlocking = checks.every(
    (c) => c.status === "ready" || c.status === "degraded",
  );
  if (!allRecognizedNonBlocking) {
    return { state: "indeterminate", canStartNewProject: false, blocking: [], degraded: [] };
  }
  return { state: "ready", canStartNewProject: true, blocking: [], degraded };
}

/**
 * The production entry point (Step 7.5): the New-Project flow calls this before allowing project
 * creation. Composes the token-bearing read-only fetch with the pure gate decision.
 */
export async function evaluateNewProjectReadiness(client: IpcClient): Promise<ReadinessGate> {
  const report = await client.getReadiness();
  return computeReadinessGate(report);
}

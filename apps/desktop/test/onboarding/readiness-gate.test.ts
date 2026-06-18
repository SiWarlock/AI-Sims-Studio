/**
 * RED — §18(4) New-Project system-readiness gate. The gate computes its OWN safety decision from
 * per-subsystem `check.status` (fail-safe allow-list); `report.overall` is advisory/display only.
 * Logic is framework-agnostic (pure function + a controller over a mock IpcClient, Lesson 4); the
 * visual gate screen rides design-fixture review (D4), not these tests.
 */
import { describe, expect, it } from "vitest";

import type {
  ReadinessCheck,
  ReadinessReport,
  ReadyState,
} from "../../../../packages/contracts/generated/contracts";
import type { IpcClient } from "../../src/ipc/client";
import {
  computeReadinessGate,
  evaluateNewProjectReadiness,
} from "../../src/onboarding/readiness-gate";

function check(
  subsystem: ReadinessCheck["subsystem"],
  status: ReadyState,
  extra: Partial<ReadinessCheck> = {},
): ReadinessCheck {
  return { subsystem, status, ...extra };
}

function report(checks: ReadinessCheck[], overall: ReadyState = "ready"): ReadinessReport {
  return { checks, overall };
}

describe("readiness gate — §18(4) New-Project system-readiness decision", () => {
  it("test_gate_blocked_when_any_subsystem_blocked — spec(§18)", () => {
    // blocked + degraded mix: blocked decides the gate AND degraded is still surfaced alongside.
    const gate = computeReadinessGate(
      report([
        check("postgres", "ready"),
        check("providers", "degraded", { detail: "key unverified" }),
        check("blender", "blocked", {
          detail: "Blender not found",
          remediation: "Install Blender 5.1",
        }),
      ]),
    );
    expect(gate.state).toBe("blocked");
    expect(gate.canStartNewProject).toBe(false);
    expect(gate.blocking).toHaveLength(1);
    expect(gate.blocking[0]?.subsystem).toBe("blender");
    expect(gate.blocking[0]?.detail).toBe("Blender not found");
    expect(gate.blocking[0]?.remediation).toBe("Install Blender 5.1");
    expect(gate.degraded.map((c) => c.subsystem)).toEqual(["providers"]); // AC: blocked surfaces degraded too
  });

  it("test_gate_ready_when_all_ready — spec(§18)", () => {
    const gate = computeReadinessGate(report([check("postgres", "ready"), check("blender", "ready")]));
    expect(gate.state).toBe("ready");
    expect(gate.canStartNewProject).toBe(true);
    expect(gate.blocking).toEqual([]);
    expect(gate.degraded).toEqual([]);
  });

  it("test_gate_allows_with_degraded_warning — spec(§18)", () => {
    const gate = computeReadinessGate(
      report([
        check("postgres", "ready"),
        check("providers", "degraded", { detail: "key present but unverified" }),
      ]),
    );
    expect(gate.state).toBe("ready");
    expect(gate.canStartNewProject).toBe(true);
    expect(gate.blocking).toEqual([]);
    expect(gate.degraded).toHaveLength(1);
    expect(gate.degraded[0]?.subsystem).toBe("providers");
  });

  it("test_gate_indeterminate_on_empty_checks", () => {
    const gate = computeReadinessGate(report([]));
    expect(gate.state).toBe("indeterminate");
    expect(gate.canStartNewProject).toBe(false);
    expect(gate.blocking).toEqual([]);
    expect(gate.degraded).toEqual([]);
  });

  it("test_gate_surfaces_every_blocking_subsystem — spec(§18)", () => {
    const gate = computeReadinessGate(
      report([
        check("blender", "blocked"),
        check("postgres", "blocked"),
        check("mods_path", "ready"),
      ]),
    );
    expect(gate.blocking.map((c) => c.subsystem).sort()).toEqual(["blender", "postgres"]);
    expect(gate.canStartNewProject).toBe(false);
  });

  it("test_gate_derives_from_checks_not_overall", () => {
    // overall claims "ready" but a check is blocked — the gate trusts the per-subsystem checks.
    const gate = computeReadinessGate(report([check("postgres", "blocked")], "ready"));
    expect(gate.state).toBe("blocked");
    expect(gate.canStartNewProject).toBe(false);
  });

  it("test_gate_fail_safe_on_unrecognized_status", () => {
    // An off-contract status (only reachable at runtime — the REST body is cast, not Zod-checked)
    // must fail CLOSED via the allow-list, never silently startable.
    const gate = computeReadinessGate(
      report([check("postgres", "ready"), check("blender", "exploded" as ReadyState)]),
    );
    expect(gate.canStartNewProject).toBe(false);
    expect(gate.state).toBe("indeterminate");
    // indeterminate reached no conclusion → surface no partial warning (both lists empty).
    expect(gate.blocking).toEqual([]);
    expect(gate.degraded).toEqual([]);
  });

  it("test_gate_all_degraded_allows_start — spec(§18)", () => {
    // A fully-impaired-but-not-missing system: every check degraded, none blocked ⇒ startable.
    const gate = computeReadinessGate(
      report([check("postgres", "degraded"), check("providers", "degraded")]),
    );
    expect(gate.state).toBe("ready");
    expect(gate.canStartNewProject).toBe(true);
    expect(gate.degraded).toHaveLength(2);
    expect(gate.blocking).toEqual([]);
  });

  it("test_gate_blocked_takes_precedence_over_unrecognized — spec(§18)", () => {
    // Precedence = blocked > indeterminate (empty/unrecognized) > ready: a known, actionable
    // blockage must never be masked behind "indeterminate" from an unrelated off-contract status.
    const gate = computeReadinessGate(
      report([
        check("blender", "exploded" as ReadyState),
        check("postgres", "blocked", { detail: "PG down", remediation: "Start Postgres" }),
      ]),
    );
    expect(gate.state).toBe("blocked");
    expect(gate.canStartNewProject).toBe(false);
    expect(gate.blocking).toHaveLength(1);
    expect(gate.blocking[0]?.subsystem).toBe("postgres");
    expect(gate.blocking[0]?.detail).toBe("PG down");
    expect(gate.blocking[0]?.remediation).toBe("Start Postgres");
  });

  it("test_evaluate_new_project_readiness_composes_client_then_gate", async () => {
    const r = report([check("postgres", "blocked")]);
    const mockClient = { getReadiness: async () => r } as unknown as IpcClient;
    const gate = await evaluateNewProjectReadiness(mockClient);
    expect(gate.state).toBe("blocked");
    expect(gate.canStartNewProject).toBe(false);
  });
});

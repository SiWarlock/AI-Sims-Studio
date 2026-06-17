# [SAFETY-RULE-6 · Inv5 · D16] Ordered approval-gate guard — the single enforcement point.
"""The 5 pipeline approval gates fire in a fixed order: plan → concept → mesh → overlay
→ export. ``GateKind`` (the frozen ``aisims_contracts`` enum) is canonical; this module
is the single enforcement point for the ordering invariant (Inv5): a gate may be
approved only when its immediate predecessor is the run's current cursor.

Depends only on ``aisims_contracts.GateKind`` (no langgraph) so the guard + its unit
pin form a standalone, bisectable safety commit.
"""

from __future__ import annotations

from aisims_contracts import GateKind

# The canonical ordered sequence of approval gates (safety rule 6).
GATE_ORDER: tuple[GateKind, ...] = (
    GateKind.PLAN,
    GateKind.CONCEPT,
    GateKind.MESH,
    GateKind.OVERLAY,
    GateKind.EXPORT,
)


class GateOrderError(ValueError):
    """Raised when a gate is approved out of the canonical plan→…→export order (Inv5)."""


def next_gate(cursor: GateKind | None) -> GateKind | None:
    """The gate admissible next given ``cursor`` (``None`` ⇒ the first gate; last ⇒ ``None``)."""
    if cursor is None:
        return GATE_ORDER[0]
    nxt = GATE_ORDER.index(cursor) + 1
    return GATE_ORDER[nxt] if nxt < len(GATE_ORDER) else None


def assert_gate_order(cursor: GateKind | None, gate: GateKind) -> None:
    """Reject approving ``gate`` unless it is exactly the successor of ``cursor`` (Inv5).

    This rejects skipping a predecessor (e.g. mesh while cursor is plan), re-approving
    the current cursor (no forward progress), and approving past the final gate.
    """
    expected = next_gate(cursor)
    if gate != expected:
        cursor_label = cursor.value if cursor is not None else None
        expected_label = expected.value if expected is not None else None
        raise GateOrderError(
            f"out-of-order gate: cannot approve {gate.value} with cursor {cursor_label!r} "
            f"(expected next gate {expected_label!r})"
        )

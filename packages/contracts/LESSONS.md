# LESSONS.md — AI Sims Creator (the shared contracts package (pydantic→TS codegen))

> Full prose for every lesson logged during work in `packages/contracts/`. The compact index lives in `packages/contracts/CLAUDE.md` "Lessons logged" table.
>
> **Lesson numbers are stable IDs.** New lessons get the next sequential number. Numbers may be referenced from code comments, commit messages, and cross-references between lessons. **Don't reorder; don't reuse a deleted number's slot.**
>
> **Lessons start at §1.** Each code area has its own lesson sequence — lessons don't carry across code areas.

---

## Lesson format

```markdown
## <a id="N"></a>N. <Short topic> — <one-line rule>

**Date:** YYYY-MM-DD.
**Source slice:** <slice-id or commit hash>.

<2-5 paragraphs explaining: what was discovered, why it matters, how to
apply the rule, what edge cases are still open. Cite file:line references
where applicable.>

**Rule:** <one-sentence summary, same as the heading subtitle>.
```

---

## <a id="1"></a>1. §2.5-seam freeze discipline — every shared contract ships a `spec(§X)` schema-snapshot in the same cycle; a drifted snapshot IS the failure

**Date:** 2026-06-17. **Source slice:** 0.2 / 0.3 / 0.4a (`c93215b`, `e7b628a`, `4a69df5`).

Every model crossing an `ARCHITECTURE.md §2.5` seam (ErrorEnvelope, IPC, domain) is frozen by a checked-in JSON-Schema snapshot test, tagged `spec(§X)`, written in the SAME `/tdd` cycle that lands the model — not a follow-up. The snapshot is generated from the approved model at GREEN and hand-verified once; thereafter a diff between `model_json_schema()` and the committed snapshot is THE test failure — never a silent regen. For a discriminated union, snapshot the full union AND separately assert exact tag membership (so a silently-dropped variant fails twice). This is what lets downstream tracks fork off frozen contracts without drift.

**Rule:** a §2.5-seam contract is not done until its `spec(§X)` schema-snapshot (+ union-membership, where applicable) ships in the same cycle; a drift is a failure, never a regen.
**Enforce:** `pin: tests/test_error.py::test_error_envelope_schema_snapshot`, `tests/test_ipc.py::test_ipc_schema_snapshot` + `::test_sse_event_union_members`, `tests/test_domain.py::test_domain_schema_snapshot`.

## <a id="2"></a>2. Enum discipline — closed enums assert exact `==` membership; open-registry keys stay `str`, never enums

**Date:** 2026-06-17. **Source slice:** 0.2 / 0.3 / 0.4a.

Two halves. (a) A CLOSED set (ErrorCode, ErrorCategory, the 13 state machines) is a `StrEnum` whose membership is asserted with `==` (exact set), not `⊆` — so adding/removing a member is a visible, intentional test change. (b) An OPEN-REGISTRY key (`archetype`, `placementCategory`, and the §11 PlacementType/FunctionalArchetype/DonorMapping keys, Invariant 6) stays `str` — validated against the registry at load time, NOT closed to an enum — even when the set looks finite today. Closing an open registry to an enum is a regression (it forecloses the project's core extensibility point). The judgment call each time: is this a fixed taxonomy (→ enum) or a data-driven registry (→ str)? `ExportMode{decor,functional,both}` = fixed → enum; `archetype` = registry → str.

**Rule:** closed taxonomies → `StrEnum` with `==`-pinned membership; open-registry keys → `str` (registry-validated), never an enum.
**Enforce:** `pin: tests/test_*.py::test_*_enum_members*`, `tests/test_domain.py::test_open_registry_keys_are_str`.

## <a id="3"></a>3. Boundary strictness — `extra="forbid"` on frozen contracts; validate STRUCTURE, not free-text content richness

**Date:** 2026-06-17. **Source slice:** 0.2 / 0.3 / 0.4a.

Frozen §2.5-seam models set `model_config = ConfigDict(extra="forbid")` — unknown fields are rejected at the boundary (deterministic validation, safety-rule-6). But "validate at the boundary" means validate STRUCTURE — closed-enum membership, numeric range (`ProgressEvent.fraction` ∈ [0,1]), collection cardinality (`AssetVariant.swatches` ≥ 1), required-field presence, no-extra-fields — NOT free-text content richness. We bound the fraction (structural) but declined `min_length` on `creatorMessage`/`maintainerDetail` (a wire contract validates shape, not message quality; non-emptiness is a producer-layer concern). The litmus test: would a reasonable, well-formed payload ever legitimately violate it? If yes (an empty-but-valid string), it's content policy → leave it out.

**Rule:** `extra="forbid"` on frozen contracts; validate structural invariants (enums, ranges, cardinality, presence), not free-text content richness.
**Enforce:** `pin: the boundary-rejection tests`; `pattern: ConfigDict\(extra="forbid"\)` present on every frozen model.

## <a id="4"></a>4. Contract scope — encode state MEMBERSHIP not transitions; the IPC error surface is an explicit endpoint→ErrorCode map ⊆ §17

**Date:** 2026-06-17. **Source slice:** 0.3 / 0.4a.

The contract encodes the STATES of a state machine (a membership-pinned enum) — never the transition edges; transitions are engine/runtime territory (Phase-2). Likewise the IPC error surface is made explicit as an `endpoint → {allowed ErrorCode}` map, asserted `⊆` the §17 `ErrorCode` enum (no stray codes) — so the UI knows exactly what each endpoint can return and a typo'd code fails the test. Cross-entity/runtime invariants (the full exportability gate, the ordered approval gates) are NOT type-encoded — they're documented + handed to a pinned, non-droppable Phase-2 validator (D16) so the safety gate can't fall through the contract→engine handoff.

**Rule:** contracts hold state membership + an endpoint→ErrorCode map (⊆ §17); transitions + cross-entity gates are pinned Phase-2 items, not contract types.
**Enforce:** `pin: tests/test_ipc.py::test_endpoint_error_code_map`; `accepted: transitions/cross-entity gates are Phase-2 validator pins (tracker D16 safety items)`.

## <a id="5"></a>5. §2.5-seam enum ownership — each shared enum has ONE home; forward-refs to absent types can't snapshot → str-now + a mandatory downstream tighten

**Date:** 2026-06-17. **Source slice:** 0.3 / 0.4 (D15/D16).

When a slice freezes before the slice that owns a type it references (IPC 0.3 before domain 0.4), you cannot forward-reference the absent type — `model_json_schema()` raises on an unresolved ref, so you can't snapshot. Resolution: the earlier slice stays domain-INDEPENDENT (str-id + protocol-level enums it owns), and any field that maps to a not-yet-existing domain enum stays `str` NOW with a **mandatory, pinned downstream tighten** (D15) — never a loose str that survives to the integration merge. And each §2.5-seam enum lives where it's canonically owned, defined once, imported elsewhere: `GateKind` (protocol/gate vocabulary) in `ipc.py` ← domain imports it; `Severity`/`ValidationScope` (validation domain) in `domain.py` ← ipc imports them. No duplicate definitions across the seam.

**Rule:** one home per shared enum (import, never redefine); freeze-before-dependency ⇒ str-now + a mandatory pinned tighten, not a forward-ref.
**Enforce:** `pin: the str→enum tighten tests land in the consumer slice (0.4b)`; `accepted: enforced by the snapshot diff + the tracker's [D15·MANDATORY] tighten bullets`.

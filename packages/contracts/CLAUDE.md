# AI Sims Creator `packages/contracts/` — Build Guide

> **You're in `packages/contracts/`.** This file plus root `CLAUDE.md` both load. The root file covers global project conventions + shared comm rules (track-prefix, escalation taxonomy, messaging budget); this file owns code-area conventions for the shared contracts package (pydantic→TS codegen).

## Launch protocol

| Working on... | cwd | Loads |
|---|---|---|
| Planning / docs / commits | repo root (`AISimsStudio/`) | root `CLAUDE.md` only |
| the shared contracts package (pydantic→TS codegen) code | `packages/contracts/` | this `CLAUDE.md` + root |

<!-- For a multi-area project, add a row per additional code area. -->

If you find yourself fighting the wrong conventions, check your cwd.

## Session start/end protocol

**At session start:**
1. Read `IMPLEMENTATION_PLAN.md` (repo root) **by section, not whole** — `grep -n "^##" IMPLEMENTATION_PLAN.md` for offsets, then Read with offset/limit just "Currently in progress" + the active phase. (The file grows; never load it whole.)
2. Confirm with the user what feature this session is targeting.
3. Read the relevant section of `ARCHITECTURE.md` from the lookup table below.

**At session end** (only when the user explicitly says we're done):

1. **Implementer runs `/session-end`.** Implementer writes ONLY:
   - `packages/contracts/` code files (the slice's implementation)
   - test files (the slice's tests)
   - dependency manifest / lockfile (deps the slice adds)
   - `docs/sessions/<NNN>-<date>-<topic>.md` (session doc, created at `/session-end` Step 5)

   **Implementer must NOT touch (all orchestrator territory).** *This list is the canonical statement
   of the territory rule — `/session-end`, the brief template, and the generated
   `scripts/guards/territory-guard.sh` PreToolUse hook (which mechanically enforces it in team mode)
   all point here.*
   - `IMPLEMENTATION_PLAN.md`
   - `packages/contracts/LESSONS.md`
   - `packages/contracts/CLAUDE.md` (entire file — both the Cross-doc invariants table AND the Lessons logged index)
   - `ARCHITECTURE.md`
   - `docs/orchestrator-briefing.md` / `docs/tdd-brief-template.md` / `docs/briefs/` / `docs/runbooks/`
   - other top-level deliverable / design docs
   - `.gitignore` and root-level dotfiles (unless adding a new artifact to ignore, flagged at Step 9)

   At Step 10: **explicit `git add <path>` per slice file; never `git add -A`/`.`; never stage an orchestrator-territory file.** Changes to any orchestrator-territory file (a new cross-doc model, a lesson, an arch note) are **flagged at Step 9**, not edited here — the orchestrator writes them hot (root `CLAUDE.md` + the Step-9 matrix).

2. **Orchestrator runs `/orchestrate-end`** for round close-out + Carry-forward triage + round terminal commit + push.

## Lookup table — where to find canonical info

Don't paste these sections into the prompt. Grep the file:section, read only what you need. `/check-arch <topic>` dispatches off this table.

| Topic | File (relative to repo root) | Section |
|---|---|---|
| py↔ts sync (pydantic→JSON-Schema→TS codegen + CI drift gate) | `ARCHITECTURE.md` | §4 |
| Model / contract inventory (frozen shared contracts) | `ARCHITECTURE.md` | Appendix A |
| Lessons logged (full prose) | `packages/contracts/LESSONS.md` | by lesson # |

<!-- Starts near-empty. Add a row whenever a topic is looked up twice. -->

**Code intelligence & docs (when available):** prefer a code-intelligence MCP / docs MCP over grep+read loops — see root `CLAUDE.md` "Code intelligence & docs."

## Stack

<!-- ▼ EXAMPLE BLOCK [id=area-stack]: stack quick-reference for implementer sessions. Canonical stack lives in root CLAUDE.md + ARCHITECTURE.md; this is the cheat sheet. ▼ -->

- **Runtime:** Python 3.13 (+ TS codegen)
- **Framework:** Pydantic v2 → JSON-Schema → TS codegen
- **Validation:** Pydantic v2
- **Lint / types / tests:** ruff / mypy --strict / pytest

<!-- ▲ END EXAMPLE BLOCK [id=area-stack] ▲ -->

## Standard commands

```bash
# Install deps (run once; re-run when the manifest changes)
uv sync

# Run the dev server (if applicable)
# (no dev server for this area)

# Tests
uv run pytest

# Quality
uv run ruff check .
uv run ruff format --check .
uv run mypy packages/contracts

# Codegen (regenerate JSON-Schema + TS types from the pydantic source)
uv run python -m aisims_contracts.codegen

# Preflight (use before saying "done" with a feature)
uv run ruff check . && uv run mypy packages/contracts && uv run pytest
```

## TDD protocol

**Write the failing test first.** Applies to deterministic code — see the TDD posture in root `CLAUDE.md` for what is test-first vs. exempt.

**Commit per slice when practical.** Never bundle a safety-critical slice with anything else.

## Forbidden patterns

<!-- ▼ EXAMPLE BLOCK [id=forbidden-patterns]: forbidden patterns — 3-5 narrow, enforceable, domain-specific rules. Shape: "Don't <pattern X> because <reason / past incident>; use <alternative Y>." Test-pin them where possible. Starts small; accretes as lessons surface. ▼ -->

Do not:

1. **Write code without a failing test first** (for deterministic code). Even one-line functions.
2. **Hand-edit the generated TS / JSON-Schema artifacts** — pydantic models are the single source of truth (§4); the TS/Node types are *generated* via `python -m aisims_contracts.codegen` and gated by the CI drift check. A hand-edit produces silent py↔ts disagreement. Edit the pydantic model and regenerate.
3. **Add or rename a field on a frozen shared contract without mirroring it in `ARCHITECTURE.md` the same round** — a frozen contract (`ErrorEnvelope`, IPC schema, provider interfaces, `BlenderJob`/`ExportJob`, registry-entry schemas, GEOM-bytes payload, Appendix-A domain types) is imported by all tracks; an unmirrored change desyncs the cross-doc invariant. Flag the change at Step 9; the orchestrator writes the model + the `§` edit hot.
4. **Drop or stop emitting `schemaVersion` / `registryVersion` / `contractVersion` on a persisted-or-negotiated contract** — versioned entities drive the migration runner (§13) and `/health` negotiation (§4); an unversioned contract breaks forward-migration and version negotiation.

**Enforcement patterns (machine-readable — `/preflight` warn-greps the staged diff against these).**
One `grep -E` (or `ast-grep`) expression per line, each tied to a numbered rule above. Rules that can't
be expressed as a pattern carry a `pin:` (test ref) or `accepted:` note on the rule itself instead.

```forbidden-patterns
# rule 2 (hand-edited generated artifacts): edits under a generated TS/JSON-Schema output path  (generated|codegen)/.*\.(ts|json)$
# rule 3 (frozen-contract field change unmirrored): pin: tests/test_arch_mirror.py  accepted: orchestrator mirrors §-section the same round
# rule 4 (dropped version stamp): pin: tests/test_versioned_contracts.py
# lesson 3 (frozen-contract boundary strictness): every frozen §2.5-seam model carries extra="forbid"  ConfigDict\(extra="forbid"\)
```

<!-- ▲ END EXAMPLE BLOCK [id=forbidden-patterns] ▲ -->

## Cross-doc invariants — schema/docs mirroring

Several typed models in this codebase are **contracts** mirrored in `ARCHITECTURE.md` and indexed in the table below. The architecture doc is the canonical contract; the model is the executable enforcement. Drift produces silent disagreement.

**Authoring discipline (orchestrator owns this table).** The implementer never edits this table or `ARCHITECTURE.md` directly — it flags a field add/remove/rename at Step 9 as a `Cross-doc invariant change`; the orchestrator writes the row + the arch edit hot the same round (see root `CLAUDE.md` + `docs/orchestrator-briefing.md`). Commits stagger; the working tree stays aligned within the round.

| Model | `ARCHITECTURE.md` section | Notes |
|---|---|---|
| `ErrorEnvelope` | §17 / Appendix A | code, category, retryable, creatorMessage, maintainerDetail, traceRef, suggestedAction — shared by all tracks · pin: `tests/test_error.py::test_error_envelope_schema_snapshot` |
| IPC contract (`ipc.py`) | §4 / Appendix A | `SseEvent` discriminated union (8 events; `error` embeds `ErrorEnvelope`) · `Endpoint` (14) + request models (multi-mode runs/gate/regenerate unions) · endpoint→`ErrorCode` map (⊆ §17) · `HealthResponse(contractVersion)` · token/idempotency header conventions. **0.4b/D15:** the 4 domain-typed SSE fields tightened `str`→enum (`StepStateEvent.status`→`StepState`; `DoneEvent.status`→`Literal[succeeded,failed,cancelled]`; `ValidationEvent.severity`→`Severity`; `.scope`→`ValidationScope`) — `ipc` now imports those 3 enums from `domain` (no longer domain-independent for the SSE surface); `GateKind` single-homed here (cycle-guarded, Lesson 5/6). Shared A↔B · pin: `tests/test_ipc.py::test_ipc_schema_snapshot` |
| IPC responses (`responses.py`) | §4 / Appendix A | REST response bodies for the 14 §4 endpoints (`RESPONSE_MODELS`, symmetric w/ `REQUEST_MODELS`), each embedding its domain entity (Project/PipelineRun/ItemSpec/FunctionalOverlay/ExportArtifact/Step; `list[Project]`+page for LIST_PROJECTS; `list[ValidationResult]` for VALIDATE; protocol acks for cancel/settings/test-provider). Imports `ipc`+`domain`; tops the intra-package DAG (`error←domain←ipc←responses`). Shared A↔B · pin: `tests/test_responses.py::test_responses_schema_snapshot` + `::test_import_direction` |
| Domain model (`domain.py`) | §12 / Appendix A / `DATA_MODEL.md` | 16 entities (Project…Trace + ExportReport; 13 top-level carry `schemaVersion`, 3 embedded: StyleBible/Swatch/ExportReport) · 13 membership-pinned state `StrEnum`s (ProjectState, ItemState 19, StepState, AssetVariantState, ConceptState, MeshState+QaStatus+CleanupStatus, OverlayState, ExportState, ExportMode, Severity, ValidationScope) · structural invariants (Inv2 same-identity ref, Inv7 ≥1 swatch, variant lineage). Open-registry keys (`archetype`/`placementCategory`) stay `str` (Inv6). Inv1/Inv5 = Phase-2 pin (D16). Shared A↔B · pin: `tests/test_domain.py::test_domain_schema_snapshot` |
| Provider adapters (`providers.py`) | §7 / Appendix A | 3 model-agnostic `Protocol` interfaces (`Image3DProvider`/`ImageGenProvider` `submit/poll/fetch` — first-arg diverges by semantics: image-to-3D `image:bytes` vs text-to-image `prompt:str`; `LLMProvider` `complete→str`/`structured→T`) + value models `ProviderJobRef` · `PollResult{status,progress?,urls?,usage?,error?}` · `ProviderUsage{latencyMs,costCents?}` (`ge=0`) · `PollStatus{submitted,running,succeeded,failed,expired}`. Open `params: dict[str,Any]` (bakeoff — Inv6-analogue, Lesson 7). Interfaces frozen by a signature test (no JSON schema for a Protocol); value models by the snapshot. Concrete adapters → 0.8/Phase-2. Shared B↔E · pin: `tests/test_providers.py::test_providers_schema_snapshot` + `::test_provider_interface_signatures` |
| Worker contracts (`workers.py`) | §8 / §9 / Appendix A | `BlenderJob`→`BlenderReport{geomBytesRef,previewRef,gateMetrics:GateMetrics,status,error?}` (+ `BBox{minCorner,maxCorner}`) · `ExportJob`→**`ExportJobReport`** (renamed from §9 `ExportReport` to avoid colliding w/ the §12 domain `ExportReport`, Lesson 8) · worker-local `BlenderJobStatus{succeeded,failed}`/`ExportJobStatus{succeeded,partial,failed}` (node maps onto domain `ExportState`). **Safety (Lesson 9):** all artifact fields are scratch-path `str` refs `min_length=1` (rule 3, never inline bytes) + a status↔outputs `model_validator` (rule 6). Shared C↔D/B↔C/B↔D · pin: `tests/test_workers.py::test_workers_schema_snapshot` + `::test_report_status_output_consistency` |
| Registry contracts (`registries.py`) | §11 / Appendix A | Open-registry entry models `PlacementType`/`FunctionalArchetype`/`DonorMapping` (id/key/name `str` — Inv6, never enums) + flexible `RuleSpec{kind,params}` rule lists (grammar S3-pinned, Lesson 10) + versioned collection wrappers `{registryVersion:int, entries}` + a pure `validate_registry(raw,type)→list[RegistryFinding{issue:RegistryIssue, error:ErrorEnvelope, entryKey?}]` (structural+version+uniqueness; Lesson 11). `validate_registry` = the eventual **load-time enforcement point for Inv6** (the domain `archetype`/`placementCategory` keys validate against these). Imports `error` only. Shared C/D↔registries · pin: `tests/test_registries.py::test_registries_schema_snapshot` |

<!-- Starts empty (or with the first model if one exists). Populated as contract models land. -->

## Module organization

<!-- ▼ EXAMPLE BLOCK [id=module-layout]: module layout + layer dependency rule. Replace with the project's real directory tree and import-direction DAG. ▼ -->

This is the **shared contracts package**: pydantic v2 models are the single source of truth → emitted as JSON Schema → codegen'd into TS (consumed by the desktop UI) + Node (consumed by the export worker), with a CI drift gate that fails on divergence (§4). It is **cross-cutting**: per §2.5 the frozen contracts are imported by all areas; it imports nothing from them.

```
packages/contracts/
  src/aisims_contracts/  # pydantic v2 source-of-truth contracts, flat modules (one per §2.5 seam):
                         #   error.py (ErrorEnvelope, §17) now; ipc.py / domain.py / providers.py /
                         #   workers.py / registries.py as 0.3–0.5 land. Each mirrored to its ARCHITECTURE.md §.
  tests/                 # unit + snapshot tests; tests/__snapshots__/ holds the checked-in JSON-Schema
                         #   snapshots (the §2.5-seam freeze guard — a drift is the failure).
  # JSON-Schema emission + py→ts/Node codegen (entry: python -m aisims_contracts.codegen) + a generated/
  # output tree (never hand-edited, forbidden-pattern 2) land in 0.6 with the CI drift gate.
```

Layer dependency direction (top depends on bottom, never reverse):

```
codegen/  →  schema/  →  models/        (codegen reads schema; schema reads the pydantic models)
generated/ is OUTPUT of codegen/ — imported BY other areas, never imported by this package
```

The contracts package sits at the **bottom** of the project import DAG (§2.5): it depends on no other area, and every other area may import its generated types. Enforce the no-upward-import rule mechanically with a test where possible — the test *is* the spec for the rule.

<!-- ▲ END EXAMPLE BLOCK [id=module-layout] ▲ -->

## Subagents

See `.claude/agents/README.md` for the canonical inventory + integration points.

<!-- ▼ EXAMPLE BLOCK [id=area-subagent-candidates]: area-specific subagent candidates — list candidates that would earn their keep specifically in this area (e.g. an ABI/types syncer for a frontend area, a Pyth/feed verifier for a contracts area). Build only on real friction. ▼ -->

Candidates (build only on real friction):
- **py↔ts drift syncer** — after a pydantic model changes, runs codegen, diffs the generated TS/Node output against the committed artifacts, and reports the drift surface for the CI gate (§4).
- **arch-mirror verifier** — checks that every frozen-contract field on a model has a matching entry in its `ARCHITECTURE.md` `§`/Appendix-A row, flagging unmirrored field add/remove/rename for Step 9.

<!-- ▲ END EXAMPLE BLOCK [id=area-subagent-candidates] ▲ -->

## Lessons logged from prior sessions

The full prose for each lesson lives in `packages/contracts/LESSONS.md`. This index is the compact orientation surface.

**Lesson numbers are stable IDs** — once assigned, they don't change. New lessons get the next sequential number. `/session-end` proposes additions when it detects them; the user approves before the entry is written and a row is added here.

Lessons start at §1.

| # | Date | Topic | Rule (one-liner) |
|--:|---|---|---|
| 1 | 2026-06-17 | [§2.5-seam freeze discipline](LESSONS.md#1) | every shared contract ships a `spec(§X)` schema-snapshot same cycle; a drift IS the failure (full union + exact membership for discriminated unions) |
| 2 | 2026-06-17 | [Enum discipline](LESSONS.md#2) | closed enums assert exact `==` membership; open-registry keys stay `str`, never enums (Inv6) |
| 3 | 2026-06-17 | [Boundary strictness](LESSONS.md#3) | `extra="forbid"`; validate structure (enums/ranges/cardinality), not free-text content richness |
| 4 | 2026-06-17 | [Contract scope](LESSONS.md#4) | encode state MEMBERSHIP not transitions; endpoint→ErrorCode map ⊆ §17; gates → Phase-2 pin |
| 5 | 2026-06-17 | [§2.5-seam enum ownership](LESSONS.md#5) | one home per shared enum (import, never redefine); freeze-before-dep ⇒ str-now + mandatory pinned tighten; canonical home sits downstream so the tighten never forces an upward import (relocate before a cycle) |
| 6 | 2026-06-17 | [`Test*`-prefix pytest collision](LESSONS.md#6) | contract models named `Test*` get auto-collected by pytest — reference them module-qualified in tests (never bare-import the `Test*` name); recurs in providers/workers (0.5) |
| 7 | 2026-06-17 | [Interface-seam freeze](LESSONS.md#7) | a `Protocol` has no JSON schema — freeze it with a signature test (method set + param names + critical types); value models get the snapshot; keep model-agnostic `params: dict[str,Any]` open (§7 analogue of Inv6) |
| 8 | 2026-06-17 | [Cross-seam name collision](LESSONS.md#8) | two §2.5 seams colliding on a name → rename the later/less-frozen one (§9 worker `ExportReport`→`ExportJobReport`); never re-freeze a landed contract to reclaim a name; fix the arch rows same round |
| 9 | 2026-06-17 | [Worker-report safety shaping](LESSONS.md#9) | worker reports carry scratch-path `str` refs (`min_length=1`, never inline bytes — rule 3) + a status↔outputs `model_validator` rejects malformed reports at the boundary (rule 6); within-model invariants belong in the contract, cross-entity gates don't |
| 10 | 2026-06-17 | [Registry envelope frozen / grammar flexible](LESSONS.md#10) | freeze a registry's entry envelope + a flexible `RuleSpec{kind,params}` rule rep; defer the rule *grammar* to the spike that pins it (S3) — over-specifying ahead is the open-seam regression (sibling to Lessons 2/7) |
| 11 | 2026-06-17 | [Pure validator function in a contracts package](LESSONS.md#11) | a contracts package may ship a deterministic validator (`validate_registry`) TDD'd with good/bad fixtures, distinct from the snapshot; take raw data in (construction failures → findings); return granular local `issue` + embedded `ErrorEnvelope`; pure + scope-bounded |

<!-- Starts empty. Each row links to its `LESSONS.md` anchor. -->

<!-- Slash commands: see root CLAUDE.md "Slash commands available." Implementer pair: /session-start + /session-end. -->

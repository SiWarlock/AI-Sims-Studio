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

**Date:** 2026-06-17. **Source slice:** 0.3 / 0.4 (D15/D16) · **0.4b** (the tighten landed, `4a69df5`→0.4b).

When a slice freezes before the slice that owns a type it references (IPC 0.3 before domain 0.4), you cannot forward-reference the absent type — `model_json_schema()` raises on an unresolved ref, so you can't snapshot. Resolution: the earlier slice stays domain-INDEPENDENT (str-id + protocol-level enums it owns), and any field that maps to a not-yet-existing domain enum stays `str` NOW with a **mandatory, pinned downstream tighten** (D15) — never a loose str that survives to the integration merge. 0.4b executed this: the 4 SSE fields retyped `str`→`StepState`/`Severity`/`ValidationScope`/`Literal[run-terminal]`, so `ipc` now imports those enums from `domain`.

And each §2.5-seam enum lives where it's canonically owned, defined once, imported elsewhere: `Severity`/`ValidationScope`/`StepState` (validation/run domain) in `domain.py` ← `ipc` imports them (0.4b). **Import-direction caveat (0.4b finding):** the tighten made the `ipc → domain` edge live, so the inverse — a future Phase-2 *domain gate model* importing `GateKind` from `ipc` — would close an `ipc ↔ domain` CYCLE. So `GateKind` stays single-homed in `ipc` and guarded for now (no domain consumer yet); when a domain gate model lands, **relocate `GateKind` to `domain.py` (or a neutral shared-enums module)** rather than importing it upward. The acyclic DAG `error ← domain ← ipc ← responses` is now pinned by `test_import_direction`, so the cycle can't land silently.

**Rule:** one home per shared enum (import, never redefine); freeze-before-dependency ⇒ str-now + a mandatory pinned tighten, not a forward-ref; the canonical home is on the *downstream* side of the import DAG so the tighten never forces an upward import (relocate the enum before creating a cycle).
**Enforce:** `pin: tests/test_ipc.py::test_sse_fields_tightened` + `::test_done_status_terminal_subset` (0.4b tighten landed); `tests/test_responses.py::test_import_direction` (acyclic DAG + GateKind cycle guard); `tests/test_responses.py::test_gatekind_single_definition`.

## <a id="6"></a>6. `Test*`-prefixed contract models collide with pytest collection — reference them module-qualified in tests, never bare-import the name

**Date:** 2026-06-17. **Source slice:** 0.4b (`responses.py`).

pytest auto-collects any class whose name starts with `Test` as a test case. Contract models named `Test…` — `TestInstallRequest`/`TestProviderRequest` (0.3) and `TestInstallResponse`/`TestProviderResponse` (0.4b) — are pydantic models, not tests, but a test module that does `from aisims_contracts.responses import TestInstallResponse` pulls the `Test*` name into the test module's namespace, where pytest tries to collect it (a `PytestCollectionWarning`, and a model with required fields can't be constructed as a test → noise/instability). 0.4b's mitigation: reference these models **module-qualified** (`responses.TestInstallResponse`) so the `Test*` symbol never enters a test module's top-level namespace. This WILL recur — providers/workers (0.5) have their own `Test*`-shaped contract names (provider "test" endpoints). A durable hardening for 0.5+: set `__test__ = False` on these model classes, or configure pytest `python_classes`, so the collision is structurally impossible rather than convention-guarded.

**Rule:** a contract model whose name starts with `Test` is collected by pytest — reference it module-qualified in tests (never bare-import the `Test*` symbol into a test module); prefer `__test__ = False` / a `python_classes` config as the durable fix when the pattern recurs.
**Enforce:** `accepted: not mechanically gated this slice — mitigated by module-qualified references; 0.5 should add `__test__ = False` / pytest `python_classes` config when the next `Test*` contract model lands`.

## <a id="7"></a>7. Freezing an INTERFACE seam — a `Protocol` has no JSON schema; freeze it with a signature test + keep its model-agnostic `params` open

**Date:** 2026-06-17. **Source slice:** 0.5a (`providers.py`, §7).

A §2.5-seam contract that is an **interface** (the §7 provider adapters `Image3DProvider`/`ImageGenProvider`/`LLMProvider` as `typing.Protocol`) has no `model_json_schema()` — the snapshot test that guards a pydantic value model can't freeze it. **Split the freeze:** the value models the interface exchanges (`ProviderJobRef`, `PollResult`, `ProviderUsage`, `PollStatus`) get the `spec(§X)` JSON-Schema snapshot; the interface itself gets a **signature-freeze test** pinning the method set + the param NAMES + the contract-critical param/return types (via `inspect`/`typing.get_type_hints`) — so a renamed param or a changed return on a frozen seam fails a test. Prefer `Protocol` (structural) over `ABC` (nominal) so mock (0.8) + real (Phase-2) adapters conform without inheriting; omit `@runtime_checkable` until an `isinstance` is actually needed (additive later). Interface first-args may legitimately diverge by semantics across separate Protocols (`Image3DProvider.submit(image: bytes)` image-to-3D vs `ImageGenProvider.submit(prompt: str)` text-to-image) — "same submit/poll/fetch" holds at method-shape level; the signature test freezes each param name.

The model-agnostic **`params: dict[str, Any]`** on `submit`/`complete` is deliberate and is the §7 analogue of **Invariant 6** (open-registry keys stay `str`): the provider seam supports a model **bakeoff with no lock-in**, so the per-model param shape is validated at the adapter-impl layer (§16), never closed to a per-model schema in the contract. Closing it would foreclose the no-model-lock-in posture — a regression, exactly like closing an open registry to an enum.

**Rule:** freeze an interface seam with a signature test (method set + param names + contract-critical types), not a JSON snapshot (that belongs to the value models it exchanges); keep model-agnostic `params` open (`dict[str,Any]`), validated at impl-time — the interface analogue of Inv6.
**Enforce:** `pin: tests/test_providers.py::test_provider_interface_signatures` (Protocol freeze) + `::test_providers_schema_snapshot` (value-model freeze).

## <a id="8"></a>8. Cross-seam name collision — disambiguate by renaming the LATER / less-frozen seam, never re-freeze a landed contract

**Date:** 2026-06-17. **Source slice:** 0.5b (`workers.py`, §9).

Two different §2.5 seams independently wanted the name `ExportReport`: the §12 **domain** `ExportReport` (0.4a, the human-readable export summary embedded under `ExportArtifact` — `projectName/timestamp/included/excluded/...`) and the §9 **worker** report (`packagePath/includedItems/resourceManifest/status/error`). Same name, different shapes, different concerns — the arch even carried the collision in two Appendix-A rows. Resolution: rename the **later, not-yet-landed** seam (the §9 worker report → `ExportJobReport`, parallel to its `ExportJob`), and leave the **already-frozen** domain `ExportReport` untouched — re-freezing a landed contract's snapshot to free up a name is churn + risk for zero benefit. The orchestrator updates the arch (§9 prose + the Appendix-A row) atomic with the round so the doc collision is also resolved. General rule for any frozen-contract package: the model that lands first owns the name; a later seam that wants it disambiguates.

**Rule:** when two §2.5 seams collide on a name, rename the later / less-frozen one (here `ExportReport`→`ExportJobReport`); never re-freeze an already-landed contract to reclaim a name; fix the arch's matching rows in the same round.
**Enforce:** `pin: tests/test_workers.py::test_export_worker_report_disambiguated` (asserts distinct symbol + distinct field set from the domain `ExportReport`).

## <a id="9"></a>9. Worker-report contracts shape the safety boundary — scratch-path refs (rule 3) + a status↔outputs `model_validator` (rule 6)

**Date:** 2026-06-17. **Source slice:** 0.5b (`workers.py`, §8/§9).

A worker job/report envelope is the sidecar↔worker boundary, so the **contract** (not just the worker impl) is the right place to shape two safety invariants. (1) **Rule 3 (sidecar = sole writer):** every artifact field on a worker report is a **scratch-path `str` ref** (`geomBytesRef`/`previewRef`/`packagePath`), never inline bytes and never a write into Postgres/the canonical tree — the worker writes to sidecar-provided scratch and returns a path. A ref field additionally gets **`min_length=1`** (an empty-string ref passes a None-presence check but is not a usable path — structural-validity, an extension of Lesson 3). (2) **Rule 6 (deterministic validation of worker output before any state write):** a `@model_validator(mode="after")` enforces **status↔outputs consistency** so a malformed report fails at the boundary — `BlenderReport`/`ExportJobReport` `succeeded ⟹ core output present AND error None`; `ExportJobReport` `partial ⟹ packagePath present` (error optional — it describes the per-item partial failure); `failed ⟹ error present`. This is a WITHIN-model invariant (like Inv7 ≥1 swatch), so it belongs in the contract — unlike cross-entity gates (Inv1/Inv5) which defer to the Phase-2 validator. The validator is `mode="after"` so the JSON schema (and 0.6 codegen) is unaffected.

**Rule:** worker-report contracts carry scratch-path refs (`str`, `min_length=1`), never inline bytes (rule 3), and a status↔outputs `model_validator` rejects malformed reports at the boundary (rule 6); within-model consistency belongs in the contract, cross-entity gates do not.
**Enforce:** `pin: tests/test_workers.py::test_report_status_output_consistency` + `::test_workers_schema_snapshot`.

## <a id="10"></a>10. Registry contract — freeze the entry ENVELOPE, keep the rule grammar FLEXIBLE when a spike will pin it

**Date:** 2026-06-17. **Source slice:** 0.5c (`registries.py`, §11).

A registry seam (§11 PlacementType/FunctionalArchetype/DonorMapping) is an **open registry** (Inv6) — entry `id`/`key`/`name` stay `str` (validated against the registry, never closed to an enum). But part of an entry is a **rule sub-grammar** (footprint / tuning-graft / eligibility / validation rules) that a later **spike pins** (S3, Phase 1 — "one archetype proves the schema"). The freeze must NOT over-specify that grammar ahead of the spike: model the rule lists as a flexible `list[RuleSpec]` where `RuleSpec{kind: str, params: dict[str, Any]}` round-trips any rule, and let S3 + the engine pin the real grammar. Closing the grammar to a typed schema now would foreclose the spike's design space — the same regression as closing an open registry key to an enum (Lesson 2) or a model-agnostic `params` (Lesson 7). The registry collection is a versioned wrapper (`{registryVersion:int, entries}`) so the §13 store can stamp + compat-check it (never drop `registryVersion`, forbidden-pattern 4).

**Rule:** freeze a registry's entry *envelope* + a flexible `RuleSpec{kind,params}` rule representation; defer the rule *grammar* to the spike that pins it — over-specifying ahead of the spike is the open-seam regression (sibling to Lessons 2/7).
**Enforce:** `pin: tests/test_registries.py::test_rule_subgrammar_representation` + `::test_open_registry_not_enum` + `::test_registry_version_present`.

## <a id="11"></a>11. A contracts package can ship a pure VALIDATOR FUNCTION (not just frozen models) — TDD'd with good/bad fixtures, distinct from the snapshot freeze

**Date:** 2026-06-17. **Source slice:** 0.5c (`registries.py`, §11 `validate_registry`).

The contracts package is mostly frozen *shapes* (snapshot-guarded), but a §2.5 seam can legitimately include **deterministic logic** — here `validate_registry(raw_data: object, registry_type) -> list[RegistryFinding]`, the §11 load-time validator. Two patterns worth reusing: (1) **take RAW data, not a constructed model** — the validator `model_validate`s inside and catches the `ValidationError`, so missing-version / malformed-entry surface as *findings* rather than uncatchable construction errors (a constructed-model-in couldn't report them). (2) **Findings are a hybrid:** a granular registry-local `issue: RegistryIssue` (clean assertions + programmatic dispatch) **plus** an embedded §17 `ErrorEnvelope` (so the eventual 0.7 store loader surfaces registry-load failures through the standard error channel) — mirroring `ValidationResult.error`. The validator is **pure** (no I/O — its production caller is the 0.7 loader) and is TDD'd like any logic (good registry → `[]`; each bad case → its finding), separate from the `spec(§11)` snapshot that freezes the shapes. Scope discipline: it validates structure + version + uniqueness only — NOT donor resolution (Donor-Library/Phase-1) or rule-semantics (S3/engine).

**Rule:** a contracts package may ship a pure, deterministic validator function alongside its frozen models — TDD it with good/bad fixtures (distinct from the snapshot); take raw data in so construction failures become findings; return a granular local `issue` + an embedded `ErrorEnvelope`; keep it pure (no I/O) and scope-bounded (structural, not semantic).
**Enforce:** `pin: tests/test_registries.py::test_validate_registry_ok` + `::test_validate_registry_rejects` + `::test_validate_registry_scope_boundary`.

## <a id="12"></a>12. Generated artifacts are committed + never hand-edited; the codegen must be DETERMINISTIC or the drift gate false-positives

**Date:** 2026-06-17. **Source slice:** 0.6 (`codegen.py`, §4).

The py→ts codegen (`models_json_schema` over all 7 contracts → combined `$defs` → `json-schema-to-typescript` → `generated/contracts.ts` + `helpers.ts`) **commits its output** as the **drift gate's diff target** (forbidden-pattern 2: never hand-edit a generated artifact — the gate enforces it; edit the model + regen). For the gate to be trustworthy the codegen must be **deterministic**: a fixed `bannerComment` (no timestamps), sorted keys, stable ordering — otherwise a clean tree emits a different-but-equivalent output every run and `--check` false-positives. **Two-level gate:** the pure-Python combined-schema `--check` (regenerate in-memory + diff committed) is the **primary** cross-track enforcement (always runnable, fully pytest-tested, no node dependency); the node TS-regen + diff catches stale TS. A gate/preflight **VERIFIES** in-sync (`--check`) — it NEVER mutates the tree (a bare regen in a preflight is a bug — cf. the `/preflight` codegen-step Finding fixed this round).

**Rule:** commit generated artifacts as the gate's diff target (never hand-edit, fp-2); the codegen must be deterministic (fixed banner, sorted keys, no timestamps) or the gate false-positives; a drift gate VERIFIES (`--check`), never mutates.
**Enforce:** `pin: tests/test_codegen.py::test_codegen_deterministic` + `::test_drift_gate_fails_on_drift`.

## <a id="13"></a>13. Forward-compatible wire enum — STRICT producer, TOLERANT consumer

**Date:** 2026-06-17. **Source slice:** 0.6 (codegen) · origin 0.2 (D10b).

A closed enum on a frozen wire contract (`ErrorCode`) stays a **STRICT** closed set on the PRODUCER side (the pydantic model — `extra="forbid"` + exact membership) so the producer can't emit a code outside the taxonomy. But the CONSUMER must **TOLERATE** an unknown code → fall back to a safe default (`SYSTEM`), so a future **additive** enum split (e.g. `PROVIDER_AUTH_QUOTA` → `PROVIDER_AUTH` + `PROVIDER_QUOTA`) is **non-breaking** for an old client. The codegen emits the tolerance as a generated `parseErrorCode(x): ErrorCode → SYSTEM` helper (a strict TS literal union + a tolerant parse), NOT a loose `| string` type. Strict model + tolerant consumers, riding `contractVersion`, is the production-grade combo for an evolvable taxonomy. (The consumer-side wiring — the UI's Zod boundary calls `parseErrorCode` — lands Phase 7.)

**Rule:** a forward-compatible wire enum is STRICT on the producer (closed + exact membership) and TOLERANT on the consumer (unknown → safe default via a generated parse helper), so an additive split is non-breaking.
**Enforce:** `pin: tests/test_codegen.py::test_errorcode_tolerance`; `accepted: consumer-side Zod-boundary wiring is Phase 7`.

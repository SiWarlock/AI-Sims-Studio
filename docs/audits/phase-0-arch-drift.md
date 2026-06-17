# Phase 0 — Architecture Drift Audit

**Branch:** `track/contract` · **Date:** 2026-06-17
**Worktree:** `/Users/dreddy/Documents/Dev/AISimsStudio-contract`
**Auditor:** arch-drift-auditor (claude-sonnet-4-6)
**Test baseline:** 70/70 contracts tests green · 60/60 pipeline tests green (130 total)

---

## Scope & Method

Anchors dispatched: **§4, §7, §8/§9, §11, §12, §17** (contracts — `packages/contracts/src/aisims_contracts/`) and **§6, §13, §14, §16** (pipeline — `services/pipeline/{engine,store,obs,adapters}/`).

Policy anchors noted but not flagged as drift: **§2.5** (coverage = union of per-seam snapshot tests), **§3** (UI shell — other track, out of scope), **§21** (numeric budgets = deliberate arch deferral).

Verification shortcut: a **GREEN schema-snapshot test** counts as verified — cited per seam. 130/130 tests pass; no failing snapshots.

---

## Per-Anchor Tables

### §17 — ErrorEnvelope (frozen contract)

All 7 `test_error.py` tests + snapshot `error_envelope.schema.json` green.

| Statement | Verdict | Evidence |
|---|---|---|
| Fields: code, category, retryable, creatorMessage, maintainerDetail, traceRef, suggestedAction | **VERIFIED** | `test_error_envelope_field_set` · `error.py:57–77` |
| code = closed StrEnum with 13 members (PROVIDER_TIMEOUT … SYSTEM) | **VERIFIED** | `test_error_code_enum_members` · `error.py:14–40` |
| category = closed StrEnum {provider, network, validation, geometry, packaging, budget, system} | **VERIFIED** | `test_error_category_enum_members` · `error.py:43–54` |
| extra="forbid" on wire boundary (safety rule 6) | **VERIFIED** | `test_error_envelope_rejects_unknown_field` |
| JSON round-trip stable (py↔ts wire form) | **VERIFIED** | `test_error_envelope_round_trip` |
| Schema snapshot frozen (§2.5 seam guard) | **VERIFIED** | `test_error_envelope_schema_snapshot` · `__snapshots__/error_envelope.schema.json` |

---

### §4 — IPC contract (frozen)

All `test_ipc.py` + `test_responses.py` + `test_codegen.py` tests green. Snapshots `ipc.schema.json`, `responses.schema.json` green.

| Statement | Verdict | Evidence |
|---|---|---|
| contractVersion = "1.0" at /health | **VERIFIED** | `test_health_response_contract_version` · `ipc.py:28` |
| 8 SSE event types {progress, step-state, log, validation, cost, gate-needed, done, error} | **VERIFIED** | `test_sse_event_union_members` · `ipc.py:148–170` |
| error SSE event embeds ErrorEnvelope (never duplicated) | **VERIFIED** | `test_sse_error_event_embeds_errorenvelope` · `ipc.py:140–145` |
| 14 REST endpoints covered with request + response models | **VERIFIED** | `test_rest_request_models_present` · `ipc.py:178–194`; `responses.py:120–135` |
| SSE domain fields tightened to §12 enums (D15, 0.4b): StepState, Severity, ValidationScope, DoneEvent Literal subset | **VERIFIED** | `test_sse_fields_tightened` · `test_done_status_terminal_subset` · `ipc.py:88–137` |
| GateKind closed enum {plan, concept, mesh, overlay, export} (5 ordered gates) | **VERIFIED** | `test_protocol_enums_membership` · `ipc.py:53–65` |
| TOKEN_HEADER + IDEMPOTENCY_KEY_HEADER on headers; mutating/read-only partition of 14 endpoints | **VERIFIED** | `test_idempotency_key_on_mutating_commands` · `ipc.py:29–33`, `319–323` |
| Per-endpoint ErrorCode map ⊆ §17 enum | **VERIFIED** | `test_endpoint_error_code_map` · `ipc.py:330–375` |
| ProgressEvent.fraction ∈ [0,1] structural constraint (safety rule 6) | **VERIFIED** | `test_progress_fraction_bounded` · `ipc.py:83–85` |
| 0.6 codegen: combined schema deterministic, covers all 7 contracts, drift gate passes | **VERIFIED** | `test_codegen_deterministic`, `test_drift_gate_passes_clean` · `codegen.py` |
| ErrorCode tolerant-consumer parseErrorCode→SYSTEM helper in generated TS | **VERIFIED** | `test_errorcode_tolerance` · `codegen.py:build_helpers_ts()` |
| IPC schema snapshot frozen (§2.5 seam guard) | **VERIFIED** | `test_ipc_schema_snapshot` · `__snapshots__/ipc.schema.json` |
| Response bodies snapshot frozen | **VERIFIED** | `test_responses_schema_snapshot` · `__snapshots__/responses.schema.json` |

---

### §7 — Provider adapters (frozen interfaces)

All `test_providers.py` + pipeline `test_mock_providers.py` + `test_mock_failure.py` tests green. Snapshot `providers.schema.json` green.

| Statement | Verdict | Evidence |
|---|---|---|
| Three Protocols: Image3DProvider (submit/poll/fetch), ImageGenProvider (submit/poll/fetch), LLMProvider (complete/structured) | **VERIFIED** | `providers.py:80–115`; `test_provider_interface_signatures` |
| ProviderJobRef = {provider, model, jobId, submittedAt, expiresAt?} | **VERIFIED** | `providers.py:57–65` |
| PollResult = {status:PollStatus, progress?, urls?, usage:ProviderUsage?, error:ErrorEnvelope?} | **VERIFIED** | `providers.py:68–77` |
| PollStatus closed StrEnum {submitted, running, succeeded, failed, expired} | **VERIFIED** | `providers.py:38–46` |
| ProviderUsage.latencyMs ≥ 0 (MUST), costCents? (SHOULD) | **VERIFIED** | `providers.py:49–54` |
| Mocks: seeded-deterministic, submit→SUBMITTED→RUNNING→SUCCEEDED lifecycle, expiresAt=submittedAt+24h | **VERIFIED** | `test_mock_provider_async_lifecycle` · `providers.py` in adapters |
| Mocks: scratch-only writes (rule 3); usage.latencyMs always set | **VERIFIED** | `test_mock_providers_conform_to_protocols`; `test_mock_provider_lifecycle` |
| Mock failure injection via FailurePlan/FailureRule/MockOp spans full §17 taxonomy (13 codes); SUBMIT/FETCH no error channel → surfaces at POLL | **VERIFIED** | `failure.py:19–27`; `test_mock_failure.py` |
| LLM sync errors raised as ProviderError carrying .envelope (no contract error field) | **VERIFIED** | `failure.py:55–64` |
| Providers schema snapshot frozen | **VERIFIED** | `test_providers_schema_snapshot` · `__snapshots__/providers.schema.json` |
| providers.py imports error only (§2.5 acyclic DAG) | **VERIFIED** | `test_providers_import_direction` |

---

### §8/§9 — Worker job/report contracts (frozen)

All `test_workers.py` + `test_mock_workers.py` tests green. Snapshot `workers.schema.json` green.

| Statement | Verdict | Evidence |
|---|---|---|
| BlenderJob = {meshPath, params, donorBBox:BBox, jobId} | **VERIFIED** | `test_blender_job_report_models` · `workers.py:74–81` |
| BlenderReport = {geomBytesRef?, previewRef?, gateMetrics?, status:BlenderJobStatus, error?}; succeeded ⟹ geomBytesRef + gateMetrics + error None; failed ⟹ error | **VERIFIED** | `test_report_status_output_consistency` · `workers.py:84–105` |
| GateMetrics = {normals:bool, uv:bool, lods:int, polyByTile:dict[str,int], meshgroups:int} | **VERIFIED** | `test_gate_metrics_model` · `workers.py:62–72` |
| BBox = two 3-float corners (cardinality-pinned) | **VERIFIED** | `test_bbox_model` · `workers.py:55–59` |
| ExportJob = {donorRef, geomBytesRef, textures, tuningEdits, targetTGIKeys, jobId} | **VERIFIED** | `test_export_job_model` · `workers.py:108–118` |
| ExportJobReport ≠ domain ExportReport (name disambiguated); {packagePath?, includedItems, resourceManifest, status:ExportJobStatus, error?}; succeeded/partial ⟹ packagePath; partial MAY carry error; failed ⟹ error | **VERIFIED** | `test_export_worker_report_disambiguated`, `test_report_status_output_consistency` · `workers.py:121–146` |
| min_length=1 on geomBytesRef/previewRef/packagePath (blank ref rejected — rule 6) | **VERIFIED** | `test_report_status_output_consistency` (blank-ref branches) · `workers.py:89,130` |
| ErrorEnvelope carries failures (not bespoke) | **VERIFIED** | `test_worker_failure_uses_error_envelope` |
| workers.py imports error only (§2.5 acyclic DAG) | **VERIFIED** | `test_workers_import_direction` |
| Workers schema snapshot frozen | **VERIFIED** | `test_workers_schema_snapshot` · `__snapshots__/workers.schema.json` |

---

### §11 — Registries (frozen entry schemas)

All `test_registries.py` tests green. Snapshot `registries.schema.json` green.

| Statement | Verdict | Evidence |
|---|---|---|
| PlacementType = {id, name, donorRef, footprintRules:list[RuleSpec]} | **VERIFIED** | `test_registry_entry_models` · `registries.py:48–52` |
| FunctionalArchetype = {id, name, donorRef, tuningGraftRules, eligibilityRules, validationRules} | **VERIFIED** | `test_registry_entry_models` · `registries.py:55–62` |
| DonorMapping = {key, donorObjectKey, requiredResources, tuningKeys, preserveKeys} | **VERIFIED** | `test_registry_entry_models` · `registries.py:64–69` |
| Rule lists typed as list[RuleSpec{kind:str, params:dict}] — open, not pre-closed (S3 pending) | **VERIFIED** | `test_rule_subgrammar_representation` · `registries.py:38–44` |
| Open registry: id/key/name are str (Inv6, never closed enums) | **VERIFIED** | `test_open_registry_not_enum` |
| registryVersion stamp on each collection wrapper | **VERIFIED** | `test_registry_version_present` · `registries.py:72–103` |
| validate_registry: structural + version + uniqueness; NOT donor resolution or rule semantics | **VERIFIED** | `test_validate_registry_ok`, `test_validate_registry_rejects`, `test_validate_registry_scope_boundary` |
| All findings carry VALIDATION_FAILED ErrorEnvelope | **VERIFIED** | `test_validate_registry_rejects` |
| registries.py imports error only (§2.5 acyclic DAG) | **VERIFIED** | `test_registries_import_direction` |
| Registries schema snapshot frozen | **VERIFIED** | `test_registries_schema_snapshot` · `__snapshots__/registries.schema.json` |

---

### §12 — Domain entities + state enums

All `test_domain.py` tests green. Snapshot `domain.schema.json` green.

| Statement | Verdict | Evidence |
|---|---|---|
| 16 entities (13 top-level persisted + 3 embedded value objects) | **VERIFIED** | `test_domain_models_present` · `domain.py:382–399` |
| Top-level entities carry schemaVersion; embedded ones do not | **VERIFIED** | `test_domain_models_present` |
| ProjectState (8 members: created→export-failed) | **VERIFIED** | `test_state_enum_membership` · `domain.py:29–38` |
| ItemState (19 members: 13 base + 6 audit-added R-d: skipped, unsupported, cancelled, test-installed, in-game-verified, in-game-failed) | **VERIFIED** | `test_state_enum_membership` · `domain.py:40–62` |
| StepState (8 members: pending, running, succeeded, failed, waiting-for-user, cancelled, retrying, skipped) | **VERIFIED** | `test_state_enum_membership` · `domain.py:65–76` |
| AssetVariantState {candidate, selected, locked, superseded} | **VERIFIED** | `test_state_enum_membership` · `domain.py:78–83` |
| OverlayState {draft, validated, approved, invalid} | **VERIFIED** | `test_state_enum_membership` · `domain.py:114–119` |
| ExportState {building, success, success-with-warnings, partial, failed, cancelled} | **VERIFIED** | `test_state_enum_membership` · `domain.py:121–128` |
| ExportMode {decor, functional, both} | **VERIFIED** | `test_state_enum_membership` · `domain.py:130–135` |
| Severity {error, warn, info, pass} | **VERIFIED** | `test_state_enum_membership` · `domain.py:138–145` |
| ValidationScope {project, item, mesh, overlay, export} | **VERIFIED** | `test_state_enum_membership` · `domain.py:147–153` |
| Open-registry keys (archetype/placementCategory) are str (Inv6) | **VERIFIED** | `test_open_registry_keys_are_str` · `domain.py:237–239` |
| FunctionalOverlay.sourceItemId is str ref (same item identity — Inv2, no duplicate) | **VERIFIED** | `test_structural_invariants` · `domain.py:289` |
| AssetVariant requires ≥1 Swatch (Inv7) | **VERIFIED** | `test_structural_invariants` · `domain.py:282` |
| AssetVariant requires conceptRef + meshRef (lineage refs, structural export-ready part) | **VERIFIED** | `test_structural_invariants` · `domain.py:280–281` |
| extra="forbid" rejects unknown fields + out-of-enum states (rule 6) | **VERIFIED** | `test_boundary_rejection` |
| JSON round-trip stable | **VERIFIED** | `test_domain_round_trip` |
| Domain schema snapshot frozen | **VERIFIED** | `test_domain_schema_snapshot` · `__snapshots__/domain.schema.json` |

**Note on §12 state membership vs. transitions:** the arch says "transitions are Phase-2 engine." The `domain.py` module docstring (`domain.py:11–14`) explicitly calls this out — correct deferral, not drift.

---

### §6 — Supervisor + single-writer lock

All `test_supervisor.py` tests green (6 tests).

| Statement | Verdict | Evidence |
|---|---|---|
| Free-port pick (kernel ephemeral bind) | **VERIFIED** | `supervisor.py:19–23`; exercised in supervisor tests |
| Spawn with start_new_session=True (process-tree isolation) | **VERIFIED** | `supervisor.py:59`; `test_supervisor_process_tree_teardown` |
| Health-poll (running-predicate Phase 0; real HTTP /health Phase 2) | **VERIFIED** | `supervisor.py:66–69`; `test_supervisor_spawns_and_health_polls` |
| Capped exponential restart-with-backoff (min(cap, base*2^i)) | **VERIFIED** | `supervisor.py:27–29`, `71–83`; `test_supervisor_restart_with_backoff` |
| Process-tree teardown via killpg (no orphan child/grandchild/port) | **VERIFIED** | `supervisor.py:85–93`; `test_supervisor_process_tree_teardown` |
| Single-writer lock: on-disk, owner-PID + heartbeat + ttl | **VERIFIED** | `lock.py:31–34`, `60–62` |
| Reclaim gated on DEAD owner PID only (live owner always holds — heartbeat stale ≠ grounds to reclaim; GC/swap safety) | **VERIFIED** | `lock.py:64–76`; `test_single_writer_lock_live_owner_with_stale_heartbeat_not_reclaimed`, `test_single_writer_lock_stale_reclaim` |
| release() idempotent | **VERIFIED** | `lock.py:78–83` |
| Phase-0 TOCTOU note documented (atomic-acquire is Phase-2) | **STALE-DOC NOTE** (see below) |

**STALE-DOC note (not a DRIFT):** `lock.py:64–70` explicitly documents the Phase-0 TOCTOU limitation ("this read-then-write is NOT atomic"). The arch at `§6` states "Atomic-acquire (close the acquire TOCTOU) + a fencing token are Phase-2." Code matches the spec's stated Phase-0 limitation — the limitation is intentional, not a gap.

---

### §13 — Store: repo layer / Alembic / versioning / write-ordering

All store tests green (16 tests across 4 test files).

| Statement | Verdict | Evidence |
|---|---|---|
| Repository layer is SOLE writer of Postgres + canonical tree (rule 3) | **VERIFIED** | `test_worker_writes_only_scratch_sidecar_commits_canonical_and_row`; `test_artifact_mover_cannot_itself_write_the_db` |
| commit_artifact holds NO DB handle (structural sole-writer guard) | **VERIFIED** | `artifacts.py` has no engine/session params; `test_artifact_mover_cannot_itself_write_the_db` |
| write-bytes-then-commit-row: bytes+fsync(file+dir) BEFORE row; crash ⟹ orphan file, never dangling row | **VERIFIED** | `test_commit_row_runs_only_after_bytes_durable`; `test_crash_at_commit_leaves_orphan_not_dangling_row` · `artifacts.py:56–85` |
| Canonical path segments sanitized (no `..`, `/`, absolute, blank) | **VERIFIED** | `test_canonical_path_rejects_unsafe_segments` · `artifacts.py:22–53` |
| Alembic baseline: project, pipeline_run, step, schema_meta tables created | **VERIFIED** | `test_alembic_baseline_builds_schema` · `migrations/versions/0001_baseline.py` |
| Migration idempotent (second run = no-op at head) | **VERIFIED** | `test_baseline_is_idempotent_to_head` |
| Every migration ships a downgrade() | **VERIFIED** | `0001_baseline.py:67–76` (downgrade drops all tables) |
| open_store stamps {schemaVersion, registryVersion, appVersion, dataDirVersion} on first open | **VERIFIED** | `test_open_stamps_then_reads_back_matching` · `versioning.py:38–43`, `facade.py:70–74` |
| open_store REFUSES incompatible stamp (schemaVersion/registryVersion mismatch) | **VERIFIED** | `test_open_refuses_incompatible_store`, `test_check_compat_accepts_match_refuses_mismatch` · `versioning.py:60–67` |
| Hybrid persistence: key columns + entity as JSONB; SQLAlchemy 2.0 async | **VERIFIED** | `models.py` (ProjectRow, SchemaMetaRow); `repository.py` |
| Repository round-trip (put → get identity) | **VERIFIED** | `test_repo_round_trip.py` |

---

### §14 — Fail-open tracing

All `test_tracing.py` tests green (3 tests).

| Statement | Verdict | Evidence |
|---|---|---|
| emit() is put_nowait — never blocks, never raises (rule 5) | **VERIFIED** | `tracing.py:45–47`; `test_tracing_fail_open_on_hang` |
| Each export runs in a fresh daemon thread with join(timeout); hang/error ⟹ drop + bump trace-loss counter | **VERIFIED** | `tracing.py:67–82`; `test_tracing_fail_open_on_hang`, `test_tracing_drop_counter_increments` |
| Spans redacted (§16) before export — no unredacted egress | **VERIFIED** | `tracing.py:68` (`redact_span` call); `test_tracing_exports_redacted_span_on_success` |
| Exporter is injected (backend-portable; Phoenix/Langfuse swap; real LangSmith Phase-8) | **VERIFIED** | `tracing.py:23–33` (Exporter Protocol); tests inject no-op/mock |
| Queue unbounded (Phase 0); bounding is Phase-8 hardening | **VERIFIED** | `tracing.py:38` (`queue.Queue()` — no maxsize) — doc note matches code |

---

### §16 — Redaction chokepoint + secrets accessor

All `test_redaction.py` tests green (6 tests, including the PINNED rule-5 test).

| Statement | Verdict | Evidence |
|---|---|---|
| Single SecretsAccessor: get(name) + active_values(); repr/str never leaks values | **VERIFIED** | `secrets.py:14–34`; `test_secrets_accessor_never_persists` |
| Redactor scrubs (a) active secret VALUES by substring, (b) enumerated PII/secret PATTERN set | **VERIFIED** | `redaction.py:52–59`; `test_redaction_scrubs_by_pattern_without_accessor` |
| PINNED: redact_envelope scrubs BOTH creatorMessage AND maintainerDetail; suggestedAction defense-in-depth | **VERIFIED** | `test_redaction_scrubs_both_errorenvelope_fields` (PINNED test); `redaction.py:68–77` |
| Fail-CLOSED: redaction error ⟹ placeholder, never raw egress | **VERIFIED** | `test_redaction_fail_closed`; `redaction.py:62–66` |
| redact_span recursive (nested dicts/lists — no nested value bypasses) | **VERIFIED** | `test_redaction_span_redacts_nested_values`; `redaction.py:79–94` |
| Egress sites wired: tracing exporter + structured logging (SSE error-event is Phase-2/7) | **VERIFIED** | `tracing.py:68` calls `redact_span`; SSE deferral consistent with `redaction.py` module docstring |

---

### §2.5 — "Freeze the seams" meta-policy

The §2.5 contract is the UNION of per-seam schema-snapshot tests (not a single model). Coverage:

| Seam | Snapshot file | Test | Status |
|---|---|---|---|
| §17 ErrorEnvelope | `__snapshots__/error_envelope.schema.json` | `test_error_envelope_schema_snapshot` | GREEN |
| §4 IPC | `__snapshots__/ipc.schema.json` | `test_ipc_schema_snapshot` | GREEN |
| §4 Responses | `__snapshots__/responses.schema.json` | `test_responses_schema_snapshot` | GREEN |
| §7 Providers | `__snapshots__/providers.schema.json` | `test_providers_schema_snapshot` | GREEN |
| §8/§9 Workers | `__snapshots__/workers.schema.json` | `test_workers_schema_snapshot` | GREEN |
| §11 Registries | `__snapshots__/registries.schema.json` | `test_registries_schema_snapshot` | GREEN |
| §12 Domain | `__snapshots__/domain.schema.json` | `test_domain_schema_snapshot` | GREEN |
| §4 Combined codegen | `generated/contracts.schema.json` | `test_drift_gate_passes_clean` | GREEN |

All 8 §2.5-seam snapshot gates: **GREEN**.

---

### §21 — Cost/budget config

Noted as a deliberate arch deferral: "no numeric SLOs (owner-locked)" / "Performance budgets: deliberate deferral." No implementation expected in Phase 0. Not audited as a contract seam.

### §3 — UI shell skeleton

UI track — not in this worktree's scope. Not audited.

---

## Summary of Findings

### DRIFT findings
*None.*

### STALE-DOC notes (code is right, spec could be clearer — not escalated)
*None.* The Phase-0 TOCTOU limitation on the lock is documented in both the arch (§6) and the code (`lock.py:64–70`) consistently.

### Ambiguous items
*None.*

---

## Verdict

All 8 §2.5-seam snapshots are green. 130/130 tests pass. No contract-vs-code mismatches found across §4, §6, §7, §8/§9, §11, §12, §13, §14, §16, §17.

**VERDICT: CLEAR**

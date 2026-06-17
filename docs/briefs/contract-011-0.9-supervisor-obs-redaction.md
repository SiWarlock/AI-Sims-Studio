# /tdd brief — supervisor_obs_redaction

## Feature
Stand up the **§6 supervisor**, the **§14 fail-open tracing seam**, and the **§16/§17 redaction chokepoint** —
the last Phase-0 slice. Skeletons + invariants, NOT real LangSmith config / real OS-keychain / real
Postgres-Blender-@s4tk supervision. **Carries the PINNED, non-droppable rule-5 safety item:** the redaction
chokepoint MUST scrub `ErrorEnvelope.creatorMessage` + `maintainerDetail` before ANY egress — its OWN commit.

## Use case + traceability
- **Task ID:** 0.9  *(third + final `services/pipeline`-area Phase-0 slice; same area/session as the store + mock slices)*
- **Architecture sections it implements:** `ARCHITECTURE.md §6` (job/run engine + **supervisor**, REQ-O-103:
  free-port pick, spawn + `/health` poll + supervised **restart-with-backoff** + **process-tree teardown** for
  Postgres/sidecar/Blender/@s4tk, no orphan ports/processes; the **single-writer lock** carrying owner-PID +
  heartbeat, stale-lock reclaim on reopen), §14 (**observability** — thin tracing seam → LangSmith, **fail-open**:
  background queue + short export timeout + **drop-on-timeout**, never stalls/fails a run; trace-loss counter;
  egress = refs not binaries), §16 (**redaction chokepoint** R-h — a **single secrets accessor** so keys never
  enter LangGraph State/logs + a structured-logging redactor + an enumerated secret/PII set, applied at **every**
  egress), §17 (the `ErrorEnvelope` whose two free-text fields the chokepoint scrubs).
- **Related context:** Phase 0, contract track (final slice before `/phase-exit 0`). Consumes **0.8's
  egress-realistic envelopes** (the synthetic secret-bearing `maintainerDetail` is the redaction test surface) and
  **0.7's `open_store`** (the single-writer lock complements the version-stamp/compat-check on open). Area
  conventions (`services/pipeline/CLAUDE.md`): `mypy --strict`, Pydantic v2; **forbidden-pattern 5** (secrets ONLY
  in the keychain, never State/logs/traces; redaction at every egress; tracing **fail-open** — never blocks a run);
  the §14 seam is portable (Phoenix/Langfuse swap) — don't hard-couple to the LangSmith SDK in the seam shape.

## Acceptance criteria (what "done" means)

**A. Supervisor (§6, REQ-O-103) — `engine/supervisor.py`**
- [ ] Free-port pick; `spawn(cmd)` of a child process; a `/health`-poll (or health-callback) loop; **supervised
  restart-with-backoff** (capped, deterministic backoff) on child exit/crash; **process-tree teardown** (no orphan
  child/grandchild processes or ports). Tested against a trivial **stand-in subprocess** (per Q4) — NOT real
  Postgres/Blender/@s4tk.
- [ ] **Single-writer lock** (per Q5): an on-disk lock carrying **owner-PID + heartbeat**; acquisition fails when a
  live owner holds it; a **stale** lock (owner PID dead AND heartbeat expired) is **reclaimable** on reopen.
  Coordinates with 0.7's `open_store` (one active project).

**B. Fail-open tracing seam (§14) — `obs/tracing.py`**
- [ ] A thin tracing seam with a **background export queue** + a **short export timeout** + **drop-on-timeout**: a
  slow / hanging / erroring / offline exporter **NEVER** stalls or fails the calling path (fail-open, rule 5 /
  R-). A **trace-loss counter** increments on every drop. The exporter is **pluggable** (a no-op/mock in Phase 0;
  real LangSmith config is Phase 8) — the seam shape stays backend-portable (Phoenix/Langfuse swap).
- [ ] Egress carries traces/metadata + artifact **references** only (binaries stay local), and passes through the
  redaction chokepoint (C) before leaving the process.

**C. [SAFETY — RULE 5 · PINNED · NON-DROPPABLE] Redaction chokepoint (§16/§17) — `obs/redaction.py` (+ secrets accessor)**
- [ ] A **single secrets accessor** (per Q2): keys are pulled at use and **never** enter LangGraph State / logs /
  traces. A structured-logging **redactor** + an **enumerated secret/PII set** applied at **every** egress.
- [ ] **PINNED, non-waivable:** the redactor **scrubs `ErrorEnvelope.creatorMessage` AND `maintainerDetail`**
  before any egress (logs / traces / SSE). **pin:** a redaction test that injects a known secret value into BOTH
  free-text fields (using 0.8's egress-realistic envelope as the fixture) and asserts **neither** survives the
  redactor; the test asserts BOTH fields by name. **This bullet cannot be waived; this is its OWN commit;**
  security-reviewer runs at Step 8.
- [ ] **Fail-closed** redaction (per Q1): if the redactor cannot run, the field is dropped/placeholdered — a raw
  free-text field is **never** egressed unredacted. (Distinct from tracing's fail-OPEN: a trace may be dropped,
  but a secret is never leaked.)

**D. Tests + preflight**
- [ ] Deterministic tests in `services/pipeline/tests/{engine,obs}/`: supervisor lifecycle (A) against a stand-in
  process; the single-writer lock acquire/contend/stale-reclaim (A); the tracing fail-open + drop-counter (B); the
  **PINNED** both-fields redaction scrub (C) + fail-closed (C); the secrets accessor never-persists guarantee (C).
  `/preflight` clean (**`uv sync --all-packages`** from workspace root — D19).

## Wiring / entry point (Step 7.5)
`none wired to a live run yet — Phase-0 skeleton.` Production callers: the **supervisor** is invoked at app
startup (Phase 2 boot / Phase-7 onboarding bootstrap status) to bring up Postgres/sidecar/Blender/@s4tk; the **tracing
seam** wraps the LangGraph nodes (Phase 2) with real LangSmith config in Phase 8; the **redactor** is called at
every egress site — the **SSE error-event** emit (Phase 2/7 IPC), structured logging (now), and the tracing
exporter (B, now). Reachability **this** slice = the supervisor controls a stand-in process end-to-end; the lock
acquires/contends/reclaims; the tracing seam drops a hanging export without blocking; the redactor scrubs both
`ErrorEnvelope` fields. The SSE-egress call site lands with the emitter (Q7) — the redactor + the envelope-scrub
helper exist + are unit-tested now.

## Files expected to touch
**New:**
- `services/pipeline/engine/supervisor.py` — free-port, spawn, health-poll, restart-backoff, process-tree
  teardown, single-writer lock (PID+heartbeat).
- `services/pipeline/obs/redaction.py` — the redactor + the enumerated secret/PII set + the `ErrorEnvelope`
  scrub helper.
- `services/pipeline/obs/secrets.py` *(or `security/secrets.py` per Q2)* — the single secrets accessor interface
  (Phase-0 skeleton; real OS-keychain is Phase-7).
- `services/pipeline/obs/tracing.py` — the fail-open background-export seam + trace-loss counter + pluggable
  exporter.
- `services/pipeline/tests/engine/test_supervisor.py`, `services/pipeline/tests/obs/test_redaction.py`,
  `services/pipeline/tests/obs/test_tracing.py`.

**Modified:**
- `services/pipeline/pyproject.toml` — only if a dep is genuinely needed (expect minimal/none — stdlib
  `subprocess`/`socket`/`threading`/`queue`; the LangSmith SDK is deferred to Phase 8). **Cleanup candidate (0.8
  note):** the 0.7 `follow_untyped_imports` override is now redundant after the D24 py.typed fix — drop it if you
  touch this file (else I'll catch it at `/orchestrate-end`).

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `services/pipeline/tests/{engine,obs}/`
1. **`test_supervisor_spawns_and_health_polls`** — spawn a stand-in; health-poll reports up. Why: §6 spawn+health.
2. **`test_supervisor_restart_with_backoff`** — child crash ⟹ supervised restart with a capped deterministic
   backoff; gives up after the cap. Why: §6 restart-with-backoff.
3. **`test_supervisor_process_tree_teardown`** — teardown kills the child (+ grandchild), no orphan process/port.
   Why: §6 process-tree teardown.
4. **`test_single_writer_lock_acquire_and_contend`** — first acquire wins; a second live acquire fails. Why: §6 lock.
5. **`test_single_writer_lock_stale_reclaim`** — a lock whose owner-PID is dead + heartbeat expired is reclaimable
   on reopen. Why: §6 stale-lock reclaim.
6. **`test_tracing_fail_open_on_hang`** — a hanging/erroring exporter never blocks or raises into the caller; the
   trace is dropped within the timeout. Why: §14 fail-open / rule 5.
7. **`test_tracing_drop_counter_increments`** — each drop bumps the trace-loss counter. Why: §14 trace-loss counter.
8. **`test_redaction_scrubs_both_errorenvelope_fields`** *(SAFETY, rule 5, PINNED)* — a known secret injected into
   BOTH `creatorMessage` and `maintainerDetail` (0.8 egress-realistic fixture) is gone post-redaction; asserts
   **both** fields by name. Why: rule 5 / §16 / §17 — non-waivable.
9. **`test_redaction_fail_closed`** — when redaction can't run, the field is dropped/placeholdered, never egressed
   raw. Why: §16 fail-closed (vs tracing fail-open).
10. **`test_secrets_accessor_never_persists`** — a secret pulled via the accessor does not appear in any
    State/log/trace surface the seam produces. Why: §16 / forbidden-pattern 5.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** **none** — the redactor CONSUMES the frozen `ErrorEnvelope`; supervisor/tracing/secrets
  shapes are `services/pipeline`-internal, not §2.5 seams.
- **Orchestrator doc rows to write hot (Step 9):** area `CLAUDE.md` lookup rows (supervisor → §6; observability +
  redaction → §14/§16); lessons (fail-open tracing; fail-closed redaction; the secrets-accessor chokepoint;
  process-tree teardown). The redaction chokepoint is a **rule-5 safety** surface — its lesson + pin are mandatory.
- **§2.5-seam touched?** No. **Safety invariant?** YES — rule 5 (redaction). The PINNED redaction bullet (C) is its
  OWN commit; security-reviewer runs (policy: `invariant`).

## Things to flag at Step 2.5
0. **(SIZE — load-bearing) split.** Large for one slice + carries a safety pin. My default: **split 0.9a/0.9b/0.9c**
   — **0.9a** supervisor + single-writer lock (`engine/`); **0.9b** redaction chokepoint + secrets accessor (`obs/`)
   — **the rule-5 SAFETY commit, on its own**; **0.9c** fail-open tracing seam (`obs/`), wired THROUGH 0.9b.
   Sequence: **0.9b before 0.9c** (nothing egresses before the chokepoint exists); 0.9a is independent. Confirm or
   propose your split. (The redaction commit is non-negotiably standalone regardless of the rest.)
1. **(LOAD-BEARING, SAFETY) Redaction match strategy + fail-closed posture.** My default: the redactor scrubs (a)
   every **active secret value** (from the accessor, at egress time, never persisted) by exact match + (b) an
   **enumerated PII/secret-pattern set** (known key prefixes/token shapes), replacing matches with a placeholder;
   applied **unconditionally** to both `ErrorEnvelope` free-text fields; **fail-closed** (redaction error ⟹ drop the
   field, never egress raw). Confirm the match strategy + fail-closed. *(If you see a materially different safety
   posture, flag it — I'll escalate as a safety design Q.)*
2. **(LOAD-BEARING) Secrets accessor shape + location.** My default: a single `SecretsAccessor` (get-by-name; values
   never persisted into State/logs/traces) — Phase-0 **skeleton** (in-memory/injected for tests; real OS-keychain is
   Phase-7 onboarding). Location: `obs/secrets.py` vs a dedicated `security/` module (the area DAG lists
   `security/redaction` as cross-cutting). My vote: **`obs/` now** (task scopes `obs/*`), relocate to `security/` if
   Phase-2 wants it broader. Confirm.
3. **Tracing fail-open mechanics.** My default: a background `queue` + a worker thread exporting with a short
   timeout; on timeout/exporter-error ⟹ drop + bump the loss counter; **never** raise into the caller; pluggable
   exporter (no-op/mock in Phase 0). Confirm the threading/queue approach + that the exporter is injected (testable
   with a hanging stub).
4. **Supervisor stand-in test strategy.** My default: drive the supervisor with a trivial child (e.g.
   `python -c` sleep/echo), asserting spawn/health/restart/teardown — NOT real Postgres/Blender. Confirm (and that
   `/health` is a callback/predicate in Phase 0, real HTTP `/health` in Phase 2).
5. **Single-writer lock home + 0.7 interaction.** My default: the lock lives in `engine/` (e.g. `engine/lock.py` or
   in `supervisor.py`), guards one-active-project, carries owner-PID + heartbeat, reclaimable when the owner PID is
   dead + heartbeat stale; complements 0.7's `open_store` version-stamp/compat-check. Confirm placement (0.9a) +
   that it does NOT duplicate the store's stamp logic.
6. **Out of scope (confirm):** real LangSmith config + the 9 EVAL harnesses (Phase 8); real OS-keychain integration
   + onboarding test-call validation (Phase 7); real Postgres/Blender/@s4tk process specifics + actual app boot
   (Phase 2); the LangGraph node instrumentation call sites (Phase 2).
7. **Redaction egress sites wired NOW vs later.** My default: 0.9 wires the redactor into the **tracing exporter**
   (0.9c) + the **structured-logging** path; the **SSE error-event** egress call site lands with the emitter
   (Phase 2/7 IPC) — but the redactor + the `ErrorEnvelope`-scrub helper **exist + are unit-tested now** (the PINNED
   test). Confirm SSE-egress wiring is Phase-2/7 (the chokepoint is ready; only the call site is deferred).

## Dependencies + sequencing
- **Depends on:** **0.1** (the scaffold — task line). Consumes **0.8** (egress-realistic envelopes — the redaction
  fixture) + **0.7** (`open_store` — the lock complements it). All landed.
- **Blocks:** `/phase-exit 0` (this is the last Phase-0 slice). Phase 2 (the supervisor boots the stack; the tracing
  seam wraps the nodes; the redactor guards every egress).

## Estimated commit count
**3** (split per Q0). The **rule-5 redaction commit (0.9b) is ALWAYS its own commit** (safety pin — never bundled).
Suggested: 0.9a (supervisor + lock) · 0.9b (redaction + secrets accessor — SAFETY) · 0.9c (fail-open tracing). If
you keep supervisor + tracing together, that's defensible — but redaction stays standalone regardless.

## Lessons-logged candidates anticipated
- **Convention candidate** — **fail-open tracing vs fail-closed redaction:** a trace may be dropped to never block a
  run, but a secret is **never** leaked — opposite postures, both mandatory (rule 5).
- **Convention candidate** — the **single secrets-accessor chokepoint**: keys pulled at use, never into
  State/logs/traces; the redactor consults the accessor's live values at egress.
- **Architecture-doc note candidate** — record the supervisor surface (free-port/spawn/health/restart/teardown +
  lock), the fail-open tracing seam, and the redaction chokepoint in §6/§14/§16 / the area `CLAUDE.md`.

## How to invoke
1. **Same `services/pipeline` implementer/session as 0.7/0.8 — already oriented; skip `/session-start`.** Read this
   brief + `ARCHITECTURE.md §6` (supervisor) + §14 (tracing) + §16 (redaction) + §17 (the `ErrorEnvelope` fields).
2. **`/tdd supervisor_obs_redaction`**.
3. **Step 2.5** — answer Q0–Q7 (Q0 split, Q1 redaction strategy + fail-closed, Q2 secrets accessor are
   load-bearing; **C is the rule-5 SAFETY pin — its own commit**); coverage map (each bullet → its test). Wait for
   `APPROVED.` before GREEN. If a genuine safety-posture fork emerges at Q1, say so — I escalate it as a safety Q.
4. **Step 9** — surface the §6/§14/§16 lookup rows + the fail-open/fail-closed + secrets-accessor lessons; the
   redaction pin is mandatory. This is the **last Phase-0 slice** → I run `/phase-exit 0` after it lands.

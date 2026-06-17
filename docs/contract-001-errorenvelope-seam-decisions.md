# ErrorEnvelope (0.2) — §2.5-seam decision input (orchestrator → lead)

> Written 2026-06-17 by `contract-contracts-orchestrator` because SendMessage **bodies** aren't reaching the lead (summaries only). Durable decision-input record for the two load-bearing `ErrorEnvelope` seam calls. Both match the brief's pre-loaded defaults; both are spec-confirmed against `ARCHITECTURE.md`. **Lead decides**; orchestrator folds the ruling into the Step-2.5 `APPROVED.` reply and (if Q1=A) the round arch-note.
>
> Kept out of `docs/briefs/contract-001-…` on purpose: the evidence cites §16, which is outside Phase 0's `Spec anchors:` line — embedding it would fail `spec-lint brief` and churn the implementer's PASS stamp.

## Q1 — `PROVIDER_AUTH/QUOTA` enum spelling

**Problem.** §17 (`ARCHITECTURE.md:283-285`) writes the code list with the slash form `PROVIDER_AUTH/QUOTA`. A Python enum identifier cannot contain `/`, so the literal spec token cannot be the member name as-is — we must pick a spelling.

**Evidence.**
- §17:289 classifies **401/402 together as one "terminal-config" class** — both → "stop, don't burn retries, creator-friendly 'check Settings'". Identical handling ⇒ one taxonomy branch today.
- Appendix-A row (`ARCHITECTURE.md:402`) lists only the field set, not the code members — no constraint either way.
- Tracker 0.2 (`IMPLEMENTATION_PLAN.md:192`) writes "PROVIDER_TIMEOUT/RATE_LIMIT/AUTH/OUTAGE", using `/` as a *separator between distinct codes* — ambiguous, not authoritative on this point.

**Options.**
- **A (RECOMMEND) — single `PROVIDER_AUTH_QUOTA`.** Keeps the §17 set at **13 codes**; identical 401/402 handling = one branch; the 401-vs-402 distinction rides in `maintainerDetail`. Requires one **Architecture-doc note**: normalize §17:284 `PROVIDER_AUTH/QUOTA` → `PROVIDER_AUTH_QUOTA` (slash→underscore) so the doc token matches the enum identifier. **Reversible** — if handling later diverges (QUOTA→"add billing/credits" vs AUTH→"re-enter key"), splitting is a clean additive enum change then.
- **B — split `PROVIDER_AUTH` (401) + `PROVIDER_QUOTA` (402).** 14 codes; mirrors the literal 401/402 distinction; but two codes *always* handled identically today = premature granularity. Requires a §17 + Appendix-A wording reconcile.

## Q2 — Does `ErrorEnvelope` carry `schemaVersion`?

**Problem.** §4:130 mandates "**all persisted entities** carry `schemaVersion`." The question is whether `ErrorEnvelope` is itself such an entity.

**Evidence — is `ErrorEnvelope` ever persisted / logged / traced STANDALONE? No.** It is always embedded in an already-versioned parent:
- §17:287 — "Carried in the **SSE `error` event**, **`Step.error`**, and **`ValidationResult`**." Those are its *only* carriers.
  - **SSE `error` event** → under **`contractVersion`** negotiated at `/health` (§4:119; Appendix-A IPC row `:403`).
  - **`Step.error`** → `Step` is an Appendix-A §12 **persisted entity** (`:412`) that carries its own `schemaVersion` (§4:130).
  - **`ValidationResult`** → Appendix-A §12 **persisted entity** (`:413`), carries its own `schemaVersion`.
- §13 (data store, `:231-239`) defines **no standalone ErrorEnvelope row/table** — Postgres persists PipelineRun/Step/ValidationResult/Trace; `error` is a *field* on them, not an independently-versioned row.
- §14 (observability, `:241-249`) — LangSmith traces are a **derived mirror**; an envelope appears as a Step's `error` field *inside* a trace (authoritative Trace summaries persist in Postgres §12, versioned). Not standalone.
- Security/redaction boundary (`ARCHITECTURE.md:278-280`) names "error envelopes" as a **redaction egress surface** (strip secrets/PII from `creatorMessage`/`maintainerDetail` before logs/traces). That is about *redaction*, not versioning — a diagnostic log line is not a re-parsed, versioned contract consumer.
- Appendix-A (`:402`) and §17 (`:283-287`) field lists **both OMIT** `schemaVersion`.

**Options.**
- **A (RECOMMEND) — NO `schemaVersion` on `ErrorEnvelope`.** Transient; always rides inside a versioned parent (SSE `contractVersion`; Step/ValidationResult `schemaVersion`). Adding it would (1) **contradict the Appendix-A + §17 field lists** = a cross-doc invariant break needing an atomic §17/Appendix-A field-add the same round, and (2) duplicate the enclosing entity's version. The wire shape is frozen by the **`spec(§17)` schema-snapshot test** (brief RED #6) — that is the drift guard, not a per-envelope version field.
- **B — add `schemaVersion`.** Contradicts §17 + Appendix-A as written; forces the atomic field-add. Only justified if we expect `ErrorEnvelope` to be persisted/exchanged **standalone** outside a versioned parent — no §ref supports that today.

## Orchestrator recommendation
**Q1 = A** (single `PROVIDER_AUTH_QUOTA`, 13 codes) · **Q2 = A** (no `schemaVersion`).
On your ruling I fold it into the Step-2.5 `APPROVED.` reply. If **Q1=A**, I queue the §17:284 slash→underscore Architecture-doc note for the round commit (atomic with the model landing). Reply with the two letters (e.g. "Q1=A, Q2=A") or your alternative.

## RESOLUTION (lead ruling, D10/D11)
**Q1 = A** (single `PROVIDER_AUTH_QUOTA`, 13 codes) · **Q2 = A** (no `schemaVersion`). Conditions:
- (a) preserve 401-vs-402 in `maintainerDetail` at emit time (docstring note in 0.2; runtime in later slices).
- (b) **extensibility guarantee** — error-code CONSUMERS tolerate unknown codes → fall back to `SYSTEM` (future additive PROVIDER_AUTH/PROVIDER_QUOTA split = non-breaking). **Layering:** 0.2 producer model stays STRICT (closed enum + RED #4 + `extra="forbid"`); tolerance lives in CONSUMERS (0.6 codegen + engine/UI) + rides contractVersion. (Interpretation flagged to lead w/ veto window before -2 snapshots.)
- (c) §17:284 slash→underscore arch-note AUTHORIZED.

## Queued round-commit actions (orchestrator — for /orchestrate-end or when the hook clears)
1. **Commit `scripts/spec-lint.sh`** — `fix(tooling): spec-lint accepts numeric task IDs`. GATED on -2's `pre-commit install` clearing the broken commit-msg hook. Do NOT let -2 stage it.
2. **ARCHITECTURE.md §17:284** — `PROVIDER_AUTH/QUOTA` → `PROVIDER_AUTH_QUOTA` (slash→underscore), atomic with the model landing. [D10/c]
3. **IMPLEMENTATION_PLAN.md 0.6** — add task: "ErrorCode codegen + consumers tolerate unknown codes → SYSTEM fallback (forward-compat; origin 0.2 / D10b)."
4. **packages/contracts/CLAUDE.md EXAMPLE BLOCK** — reconcile package name `contracts` → `aisims_contracts` (+ `contracts.codegen` → `aisims_contracts...`), per Q3.
5. **packages/contracts/CLAUDE.md cross-doc ErrorEnvelope row** — add `pin: tests/test_error.py::test_error_envelope_schema_snapshot` (row already exists).
6. **IMPLEMENTATION_PLAN.md** — tick 0.1 + 0.2 on completion; log D7/D8 (pre-commit+gitleaks scope), D10/D11 (Q1=A/Q2=A).
7. **Lessons** — route -2's Step-9 candidates (extra="forbid" on frozen §2.5-seam contracts; closed-enum exact-membership; §2.5-seam ships a spec(§X) schema-snapshot same cycle) to packages/contracts/LESSONS.md + CLAUDE.md index when Step-9 lands.
8. **Brief commit** — `docs/briefs/contract-001-…` (PASS @28408bb0) + this decision file land at the round commit.

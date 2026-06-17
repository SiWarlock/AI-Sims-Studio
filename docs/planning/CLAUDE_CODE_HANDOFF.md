# Claude Code Handoff — AI Sims Creator

## Goal
Review the architecture **draft** + all supporting planning docs, run a second-pass gap audit, finalize the
binding `ARCHITECTURE.md`, and only then generate `IMPLEMENTATION_PLAN.md` from the project's task template.
This package was produced by `/arch-draft` (Brain 1); you are **Brain 2** (`/arch-finalize`) — a deliberate
cross-model adversarial pass.

## Build Posture
**production-grade** — confirmed by the user at planning start, on a **narrow-but-open** product surface.
Finalize and audit **against it:** treat missing production concerns (error paths, idempotency, observability,
secrets, deploy/rollback, durability/resumability) as **critical gaps**. Scope is constrained (the MVP feature
set + open registries), but engineering quality is not deferrable. The anchor "demo" = the **Y2K end-to-end run
+ in-game test-install** (not optional here — it's the acceptance bar).

## Inputs (read ALL end-to-end)
- `PRD.md` (source PRD v2)
- `docs/planning/PRESEARCH.md` (Phases 0–9: intake, mechanics, users, requirements, constraints, scope, assumptions/open-Qs)
- `docs/planning/RESEARCH.md` (R-001…010 — image-to-3D, local-Mac, **DBPF tooling**, Sims format, orchestration, shell, observability, Blender, concept-image, evals; + eval-deepdive addendum)
- `docs/planning/DECISIONS.md` (ADR-001…014, all **Locked**, each with fallback + invalidation)
- `docs/planning/DATA_MODEL.md` (entities, state machines, invariants, open registries)
- `docs/planning/USER_FLOWS.md` (flows A–K + requirement→flow coverage)
- `docs/planning/RISKS.md` (register + trust boundaries; R1–R3 are the spike drivers)
- `docs/planning/ARCHITECTURE_DRAFT.md` (this draft; anchors `#sec-1`…`#sec-23`)
- `docs/planning/DIAGRAM_PLAN.md`
- the project's `IMPLEMENTATION_PLAN.md` template (when generating tasks)

## Instructions
1. Read all docs end-to-end. **Do not start implementation.**
2. Run the **gap audit** (below), honoring the production-grade posture.
3. Identify inconsistencies, missing decisions, unclear boundaries, untestable requirements, scope creep, and
   under-built production concerns.
4. Propose precise edits to the architecture; **confirm load-bearing changes with the human**.
5. Apply confirmed edits → produce the binding `ARCHITECTURE.md` (repo root) from the project's
   `templates/ARCHITECTURE.md`, preserving the `#sec-` anchors (downstream binds to them).
6. Only then generate `IMPLEMENTATION_PLAN.md`: every task references a `#sec-` anchor; **do not invent
   architecture**; if a task needs absent architecture, **flag it** before adding.
7. **Build order = spikes-first** (de-risk before breadth), then invariants/lifecycle/tests, then hardening:
   - **S1 — Sims DBPF/GEOM export spike** (R1, the #1 risk): prove @s4tk clone-a-donor + a headless GEOM path
     produces a **placeable** object via **test-install**, or trigger a fallback (custom GEOM writer / Windows
     helper / pinned-old-Blender microservice). *Nothing downstream is real until this is settled.*
   - **S2 — image-to-3D bakeoff** (Hunyuan3D-2.x vs Tripo3D v2.5 vs TRELLIS on real Sims props).
   - **S3 — functional tuning-clone spike** (one archetype, e.g. light or mirror, working in-game).

## Gap Audit (≈13 dimensions)
Look for: missing user flows · missing lifecycle states · missing failure modes · missing interfaces/schemas
(IPC, provider, worker, registry contracts) · unclear source-of-truth · unresearched external deps · inconsistent
decisions · overbuilt scope (open ceiling + no timebox = watch R14) · missing tests/eval mappings · missing
deploy path (macOS sign/notarize/bundle-Postgres) · missing security/trust boundaries · missing diagram needs ·
missing task-planning anchors. Return: (1) Critical gaps (2) Important gaps (3) Nice-to-haves (4) Proposed edits
(5) Questions requiring human decision.

## Build posture & still-open items to resolve in finalize
- **Posture:** production-grade (audit against it).
- **Artifacts written by Brain 1:** PRESEARCH, RESEARCH, DECISIONS, DATA_MODEL, USER_FLOWS, RISKS,
  ARCHITECTURE_DRAFT, DIAGRAM_PLAN, this handoff (planning mode = Standard + DATA_MODEL/USER_FLOWS/RISKS).
- **Still-open / research-required (resolve or carry as flagged):**
  1. **R1 GEOM export feasibility** — *the* gating unknown; S1 must settle the concrete approach (add-on vs
     custom writer vs helper). Architecture must keep all three fallbacks viable.
  2. **Claude subscription/OAuth auth** for a custom app — likely unsupported; default to Anthropic **API key**
     / OpenRouter (ADR-14). Verify, don't architect around the subscription.
  3. **Local-3D MPS fallback** — community fork viability (ADR-11); keep feature-flagged/optional.
  4. **OpenRouter image-to-3D coverage** — verify (it routes LLM/image, not necessarily 3D).
  5. **Mac-side Sims tooling longevity** (@s4tk pre-release; GEOM provenance) — vendor-pin + round-trip CI.
  6. **Cross-platform (Windows)** — deferred; keep architecture portable (ADR-13).
- **Frozen-first contracts** (Brain 2 should pin these in ARCHITECTURE.md §6/§4a before tracks fan out): IPC
  schema, domain types, provider interfaces, worker contracts, registry schemas.

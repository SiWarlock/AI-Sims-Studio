# PRESEARCH — AI Sims Creator

> **Stage:** arch-draft (Brain 1) rough-draft planning artifact. Consolidated pre-research doc.
> Domain-model / user-flow / risk detail is split into `DATA_MODEL.md`, `USER_FLOWS.md`, `RISKS.md`
> per the chosen planning mode. This file is a **rough draft** for adversarial finalization by
> `/arch-finalize`.
>
> **Source PRD:** `PRD.md` (AI Sims Creator PRD v2, dated 2026-06-16).

**Tag legend:** `locked decision` · `proposed recommendation` · `open question` · `scope simplification`
(posture-gated cut) · `production-hardening` (load-bearing under production-grade) · `deferred work` ·
`research required`.

---

## Phase 0 — PRD Intake

### Product in One Sentence
A desktop AI studio that turns a natural-language prompt into a reviewable, installable **Sims 4
Build/Buy custom-content collection**, via a staged, graph-orchestrated, observable pipeline:
*prompt → collection plan + style bible → concept images → image-to-3D mesh → Blender cleanup/preview →
Sims archetype mapping → optional functional overlay → validation → export.*

### What the Product Is
- A **structured, observable, resumable creation pipeline** with explicit product states, repeatable
  jobs, human review gates, pluggable model/tool **adapters**, and eval harnesses.
- A **full creator-facing desktop app** (11 screens) plus an advanced/developer panel.
- A system where **UI and pipeline are decoupled** through stable contracts + mock adapters, so both
  can be built in parallel.

### What the Product Is Not
- Not a generic chatbot or an unconstrained AI agent.
- Not a universal mod generator; not CAS (clothing/hair/makeup), animation, or arbitrary gameplay
  scripting (all explicit non-goals).
- Not a guaranteed "any prompt → any object" generator. Scope is constrained to ~7 decorative
  Build/Buy categories + 4 functional archetypes (audio, light, mirror, moodlet; computer-prop optional).

### Primary Problem
A Sims creator with strong creative direction but no modding/Blender/packaging skill cannot today turn
a themed idea into installable, coherent Build/Buy content without operating a complex, brittle,
multi-tool pipeline. This product automates and gates that pipeline behind a simple creator UI.

### Primary User
- **Primary:** non-technical Sims 4 creator — strong aesthetic/gameplay sense, describes collections
  clearly, wants fast iterative visual review + regeneration, must not need package internals.
- **Secondary:** technical maintainer — operates logs/traces/adapters/reruns/evals via the dev panel.
- **Implementation user:** the coding agent that builds from PRD + this planning chain.

### Core Workflow
Create project → enter collection prompt (+ optional required items, style notes, item count, output
mode, generation mode) → system generates collection plan + style bible → user edits/approves plan →
per-item concept images → user approves/regenerates concepts → image-to-3D mesh candidates → mesh QA →
Blender cleanup/normalize/preview → archetype mapping → curate on Collection Board / Item Detail →
optional functional overlay via wizard → validation center → export center → installable Sims 4 content
+ export report. **Anchor scenario:** the Y2K Bedroom Clutter set, proven end-to-end with ≥1 functional
upgrade (CD-player vertical slice).

### Explicit PRD Requirements (load-bearing, abridged — full list lives in PRD §§12–26)
- 11 UI screens (UI-001…UI-011) incl. dashboard, wizard, plan review, generation workspace, concept
  review, collection board, item detail, functional wizard, validation center, export center, dev panel.
- Stable pipeline interface (PIPE-001) with **mock + real adapters** (PIPE-002/003), **resumable jobs**
  (PIPE-004), and **human review gates** (PIPE-005).
- Image-to-3D **adapter layer**, multi-candidate meshes, mesh QA, structured failure (FR-3D-*).
- Blender automation **strategy spike** — deterministic Python vs MCP/agentic vs hybrid (BLEND-*, §15).
- Graph orchestration with step-level state + repair loops + interruptions (ORCH-*).
- Observability: trace every run, artifact lineage, user-review events (OBS-*).
- 9 eval harnesses (EVAL-001…009) including the image-to-3D model bakeoff.
- 11 product entities (§20), functional overlays as **extensions of assets** (not duplicates).
- Validation at concept/mesh/item/overlay/project levels (§23); export modes + report (§24).
- 18 product-level acceptance criteria (AC-001…018) + vertical-slice + UI acceptance criteria (§26).

### Implied Requirements (not spelled out, load-bearing)
- A **language/runtime split**: pipeline is Python-centric (graph orch, PyTorch image-to-3D, Blender
  `bpy`); UI wants a JS/TS desktop stack → an **IPC / contract boundary** between them is the system spine.
  `research required` / decided in Phase 11.
- A **local project store + artifact store** with a stable on-disk layout (by project/item/candidate),
  schema versioning, and migration. `production-hardening`.
- A **job/run engine** distinct from the graph: queueing, cancellation, retry, progress streaming to UI.
- A **provider/secrets/config layer** for cloud model API keys (cost + rate limits + failure modes).
- **DBPF / Sims 4 package writing** is the true "installable" gate and is the least-specified, highest-risk
  subsystem — needs its own research + design. `research required`.

### External Dependencies
- **Image-to-3D** model providers — cloud-first (WaveSpeed, Replicate, fal, etc.); local Apple-Silicon
  option pending a capable model. Candidates: SF3D, SPAR3D, TripoSR, TripoSG, TRELLIS/TRELLIS.2,
  Hunyuan3D 2.x.
- **Concept image generation** (text→image) provider(s).
- **LLM** for planner / style-bible / concept-prompt / archetype-mapper / repair workers.
- **Blender** (local automation engine via `bpy`; optional Blender MCP).
- **Graph orchestration** framework (LangGraph or equivalent).
- **Observability** platform (Langfuse / Phoenix / LangSmith / OTel).
- **Sims 4 packaging** tooling/format (DBPF) + a configured local Mods/test-install folder.

### Ambiguities / Open Questions (carried into later phases)
- PRD §29's 15 open questions (desktop framework, storage format, orch framework, observability tool,
  best concept-image model, first image-to-3D adapter, hardware/exec model, Blender install/invoke,
  Blender spike outcome, export/package builder, min Sims-output acceptance checks, test-install
  MVP-or-not, default concept/mesh candidate counts, preview/thumbnail style).
- **What "installable Sims 4 content" concretely requires** (DBPF structure, OBJD/MODL/GEOM/etc.,
  catalog metadata, thumbnails) — the deepest unknown. `research required`.
- Functional overlays: how far "behaves like an audio/light/mirror object in-game" actually goes for
  MVP vs a metadata-only stub. `open question`.

### Initial Risk Areas (full register in `RISKS.md`)
- Image-to-3D quality variance; Blender automation brittleness; UI blocking on slow jobs; functional
  scope creep; pipeline unobservability; coding-agent overbuild (PRD §28). **Plus:** DBPF/export
  fidelity ("looks done but isn't actually placeable in-game"), cloud cost/rate-limit blowups, and the
  Python↔UI IPC boundary becoming a bug surface.

### Recommended Planning Mode
`locked decision` — **Standard + `DATA_MODEL.md`, `USER_FLOWS.md`, `RISKS.md`.** Detailed PRD, large
multi-subsystem build; rich domain model and user-flow set justify splitting those three out.

### Build Posture
`locked decision` — **Production-grade.** The product *scope* is a deliberately constrained MVP, but the
PRD's own guardrails demand production engineering: observability/tracing from day one, eval harnesses
from the start, failure states before happy paths, validation gates, resumable jobs, clean adapter
boundaries, local-first project safety. Cuts are explicit, flagged deferrals — never silent. A demo
(the Y2K anchor) is the natural near-final slice but the system is built to run and be maintained.

### Confirmed Environment & Constraints (Phase-0 interview)
- `locked decision` **Compute — image-to-3D:** cloud-first via hosted-GPU providers (WaveSpeed /
  Replicate / fal / OpenRouter-style). Local **Apple Silicon Mac, 48 GB unified RAM** is a viable
  fallback **iff** a capable Mac-runnable model is found. → Image-to-3D adapter layer MUST support both
  remote-HTTP and local-process execution behind one interface. *(Note: OpenRouter routes LLM/image
  models, not image-to-3D — verify 3D coverage in Phase 10.)* `research required`
- `proposed recommendation` **Compute — Blender:** runs **locally** on the Apple Silicon Mac (48 GB is
  ample); containerization deferred. Revisit if cloud-Blender simplifies reproducibility.
- `locked decision` **Hardware of record:** Apple Silicon Mac, 48 GB RAM, macOS (dev + primary run target).
- `locked decision` **Distribution:** a few known users → shareable build, light packaging; installers /
  code-signing / auto-update / broad cross-platform are **deferred work**, not MVP baseline. Cross-platform
  (Windows, where many Sims players are) is an `open question` for Phase 2/7.

---

## Phase 1 — Product Mechanics

### Core Object of Value
A **collection** of **items**. Each item resolves to one **asset variant** (chosen concept + chosen mesh +
swatches + preview), optionally extended by a **functional overlay**, and exported as installable Sims 4
content. The unit of value = *one in-game-placeable Build/Buy object* (decorative, or decorative+functional).

### State-Changing Actions
create project · generate plan · edit/approve plan · generate concept candidates · approve/reject/regenerate
concept · generate mesh candidates · run mesh QA · run Blender cleanup · render preview · select variant ·
generate swatches · edit metadata · include/exclude · make functional (attach overlay) · validate (per
scope) · build export · test-install · rerun/retry/cancel a step.

### Lifecycle (three nested clocks)
- **Project:** created → planned → generating → curating → validating → exported.
- **Item (13 statuses, PRD UI-004):** planned · concept-pending · concept-generating · concept-review-needed
  · mesh-pending · mesh-generating · mesh-QA-pending · blender-cleanup-pending · preview-ready · needs-review
  · export-ready · failed · excluded.
- **Run/step (8 states, PRD ORCH-002):** pending · running · succeeded · failed · skipped · waiting-for-user ·
  retrying · cancelled.

### Units / Records
items · concept candidates · mesh candidates · asset variants · swatches · functional overlays · pipeline
runs + steps · traces · validation results · export artifacts + report · human-review/preference events.

### Who/What Creates the Main Objects
user (project, prompt, approvals, edits) · Collection Planner + Style Bible Generator (plan, item specs,
style bible) · Concept Prompt + Image generators (concepts) · 3D Model Router (mesh candidates) · Blender
Cleanup worker (normalized mesh + preview) · Archetype Mapper (archetype assignment) · Functional Overlay
Planner (overlays) · Package/Export Builder (export artifacts).

### Who/What Resolves / Completes Them
Human review gates (plan / concept / mesh / overlay / export approvals) + validation worker + export
builder + (now) **test-install verification** as the in-game "done" check for the anchor slice.

### Hidden Mechanics (inferred, confirmed)
- **One asset, multiple outputs:** decor identity and functional identity are the SAME item; overlay is an
  extension; export emits decor-only / functional-only / both. `locked decision` (data-model invariant).
- **Candidate→accepted funnel + lineage:** N concept candidates → 1 approved; N mesh candidates → 1 selected
  variant; every artifact chains mesh ← concept ← item-spec ← plan ← prompt (OBS-003 lineage).
- **Style bible is collection-level** and constrains every item's concept prompt (style-lock, should-have).
- **Repair loops are scoped** per-item, per-stage.
- **Unsupported requests** resolve as: convert-to-nearest-supported (with confirmation) OR mark-unsupported
  with a creator-friendly reason (PRD §10.3).

### Confirmed "Playable In-Game" Mechanics (Phase-1 interview) — SCOPE-DEFINING
- `locked decision` **CC technique = clone-and-replace an EA object** (the canonical Sims 4 Studio workflow):
  clone an EA catalog/functional **donor** object → swap mesh (GEOM) + textures → retune catalog
  metadata/IDs → write a DBPF `.package`. Functional objects additionally **clone the donor's tuning** so
  behavior comes along. Exact scriptable tooling (S4S CLI vs community DBPF lib vs custom writer) is
  `research required` (Phase 10) + an export spike.
- `locked decision` **(SCOPE-ELEVATING) Decorative export bar = real & placeable in-game for ALL exported
  items.** Not a scaffold. Every exported decorative item must produce a valid DBPF clone with game-ready
  GEOM + LODs + textures + catalog metadata + thumbnail and actually appear/place in Build/Buy. → makes the
  **Sims export (DBPF/GEOM/catalog)** subsystem first-class and load-bearing; the Blender pipeline must
  output *game-ready* geometry (LODs, footprint/slots, correct scale/orientation/origin/rig). **#1 risk.**
- `locked decision` **(SCOPE-ELEVATING) Open, extensible registries — NOT fixed lists** (Phase-10 reframe).
  The PRD's "7 decorative categories" and "4 functional archetypes" are replaced by data-driven, extensible
  registries so the user is **never boxed into a fixed item set**:
  - **Decorative generation is fully open** — any prop. What's finite is the **placement-type registry**
    (surface/table · floor · wall · shelf · ceiling · …), each mapped to an EA donor (footprint/catalog slot).
    Adding a placement type = a config entry, not code. Decorative breadth ≈ unlimited.
  - **Functional behavior = an extensible archetype registry** — each entry =
    `{behavior → EA donor + tuning-graft rules + eligibility + validation}`. Adding a functional archetype =
    registry entry + donor mapping + test (**no engine rewrite**).
- `locked decision` **(SCOPE-ELEVATING) Functional depth = "as many as feasible," registry-extensible.**
  Seed the registry with as many working in-game behaviors as the spikes prove out (audio/light/mirror/moodlet
  are the obvious seeds; light/mirror likely simplest donors). Open ceiling; bounded only by "has an EA
  behavior to clone." → **tuning-clone/overlay** subsystem is large and load-bearing (**#2 risk**); sequenced
  behind a single-archetype spike to learn cost before breadth. Consistent with no-timebox/correctness-first.
- `locked decision` **The one out-of-scope frontier = arbitrary NOVEL scripted gameplay** (behavior no EA
  object already has). This is a *feasibility wall* (authoring game logic, not generating assets), not an
  arbitrary limit — stays the PRD §4.3 non-goal.
- `locked decision` **Verification loop:** no Sims 4 install yet, but the user **will install it**, so
  **test-install + manual in-game placeability/behavior check is part of the MVP loop** (lifts test-install
  from should-have → must-have). Target = local Mods folder on the Apple Silicon Mac (Sims 4 has a Mac build).

### Still Ambiguous (→ later phases / research)
- Exact DBPF resource set required per archetype (OBJD/MODL/MLOD/GEOM/RIG/FTPT/thumbnail/tuning) and which
  EA donors to clone per archetype — `research required` (Phase 10) + spike.
- Whether generated meshes can realistically be made game-ready (LODs/footprint/rig) by automated Blender
  vs needing heavy manual fallback — `open question`, the central feasibility risk; spike decides.
- Mac-side Sims-tooling maturity (most CC tooling is Windows/.NET, e.g. Sims 4 Studio) — `research required`.

---

## Phase 2 — Users and Actors

### Primary User — Sims Creator
- **Role:** non-technical Sims 4 content creator. **Goal:** turn a themed idea into installable Build/Buy
  content fast, iteratively, without touching package internals.
- **Context:** desktop app, local-first. **Pain points:** modding/Blender/DBPF toolchains are brittle and
  expert-only. **Success:** a coherent, in-game-placeable collection exported. **Failure:** opaque errors,
  lost work, junk meshes, content that won't load in-game.

### Secondary User — Technical Maintainer
- **Role:** builds/debugs/tunes the pipeline (often the same person + the coding agent). **Goal:** observe
  runs, switch adapters, rerun failed steps, run evals, inspect artifacts/traces. Uses **Advanced/Dev mode**.

### Non-Human Actors
~15 worker roles (orchestrator, collection-planner, style-bible, concept-prompt, concept-image, 3D-router,
mesh-QA, blender-cleanup, swatch, archetype-mapper, overlay-planner, export-builder, validation, repair,
human-gate) · external APIs (LLM, image-gen, cloud image-to-3D) · local **Blender** process · the
**job/run engine** · the **observability backend**.

### Permission / Mode Matrix (no accounts)
| Actor | Can Do | Cannot Do | Risk |
|---|---|---|---|
| Creator (default mode) | full creative workflow, approvals, regenerate, export, test-install | see raw logs/traces/adapter config; bypass validation gates | confusion if internals leak into creator UI |
| Maintainer (Advanced mode) | all creator actions + rerun steps, switch mock/real adapter, view traces/artifacts/evals, export logs | — | misconfiguration; cost via manual reruns |
| Agents/workers | call tools through explicit interfaces; write **validated** state only | write unstructured project state directly; accept MCP output without deterministic validation (MCP-003) | state corruption if a worker bypasses validation |
| External APIs | return artifacts/results on request | mutate project state directly | cost, rate-limits, outages, nondeterminism |

`locked decision` **No auth / accounts / multi-user.** Single local user; cloud API keys stored as **local
secrets** (OS keychain / encrypted config) — `production-hardening`, not a user-account system.

---

## Phase 3 — Stakeholders and Reviewers

| Stakeholder | Cares About | Would Reject If | Evidence Needed | Architecture Must Address |
|---|---|---|---|---|
| You (product owner + acceptance) | anchor scenario works; real in-game output; maintainable | Y2K set can't go end-to-end; export not actually placeable | anchor run + AC-001…018 + in-game test-install | full pipeline + real DBPF export + verification loop |
| The few known creator-users | simple creator UX; reliable results | UI exposes internals / breaks on slow jobs | usable creator mode; progress + recovery | mode separation, async UX, scoped retry |
| Technical maintainer | observability, adapter swap, reruns, evals | unobservable pipeline; can't debug or swap models | dev panel + traces + eval harnesses | tracing day one, adapter boundaries, eval scaffolding |
| Brain 2 (`/arch-finalize`) + coding agent | buildable, anchored, gap-free architecture | thin sections, unmapped requirements, unresolved load-bearing decisions | anchored ARCHITECTURE.md + this artifact set | stable anchors, decisions locked or flagged open |

No CISO / compliance / legal / investor stakeholders in scope.

---

## Phase 4 — User and System Flows
See `USER_FLOWS.md` for the full flow set (Workflows A–F + system flows G–K) with the confirmed
**bounded-parallel** execution, **reconcile-and-resume** recovery, **soft-budget** cost behavior, and
per-flow success/failure/recovery/data-touched detail. Confirmed flow-shaping decisions:
- `locked decision` **Execution:** bounded-parallel item generation with a **configurable concurrency cap**
  (default ~2–4 in flight); **one project actively generating at a time**.
- `locked decision` **Recovery:** on reopen, **detect interrupted runs + reconcile in-flight cloud jobs by
  re-polling provider job IDs** where possible, then offer resume/retry from last completed step; accepted
  assets never lost. `production-hardening`.
- `locked decision` **Cost/volume:** generation mode → default candidate counts (Fast ≈1/1, Balanced ≈2/2,
  Quality ≈3+/3+), per-item override; **running cost estimate + warn-before-large-run** (soft budget, no
  hard block for MVP). Hard caps = `deferred work`.

---

## Phase 5 — Domain Model
See **`DATA_MODEL.md`** — 16 entities, relationships, 6 state machines (project / 13-state item / 8-state
run-step / concept / mesh / overlay+export), 10 invariants, glossary. `locked decision` **swatches =
Sims-native, multi-swatch (multiple recolors) in MVP**; *variant* = alternate mesh candidate.

---

## Phase 6 — Requirements

**Baseline (explicit, cited):** the PRD's own IDs are adopted verbatim and carry their PRD citation —
`FR-PROJ-*, FR-PLAN-*, FR-CONCEPT-*, FR-3D-*, FR-BLEND-*, FR-CURATE-*, FR-FUNC-*, FR-VAL-*, FR-EXPORT-*,
FR-DEV-*` (PRD §21); NFRs (PRD §22); validation (§23); export (§24); acceptance `AC-001…018` + vertical-slice
+ UI acceptance (§26); evals `EVAL-001…009` (§19); observability `OBS-001…005` (§18); orchestration
`ORCH-001…006` (§16); pipeline `PIPE-001…005` (§13). `/arch-finalize` will persist the full PRD→REQ
coverage table; this section records only the **interview-derived** requirements the PRD did not state.

### Interview-derived requirements (new — `user-confirmed` unless noted)
| ID | Requirement | Source | Priority | Acceptance signal |
|---|---|---|---|---|
| REQ-F-101 | Decorative export produces **real, in-game-placeable** DBPF for **every** included item (not a scaffold) | user-confirmed (Phase 1) — *elevates* AC-015 | must-ship | item appears + places in Build/Buy on real install |
| REQ-F-102 | **Extensible functional-archetype registry**; seed "as many as feasible" working in-game behaviors (audio/light/mirror/moodlet seeds); adding one = registry+donor+test, no engine rewrite | user-confirmed (Phase 1 + Phase-10 reframe) — *supersedes/elevates* AC-013 | must-ship | ≥1 archetype works in-game; new archetype addable via registry |
| REQ-F-103 | Export uses **clone-and-replace of an EA donor** object (data-driven DonorMapping registry) | user-confirmed (Phase 1) | must-ship | package built from donor; loads in-game |
| REQ-F-106 | **Open registries (no fixed enums):** decorative generation open for any prop; **placement-type** + **functional-archetype** registries are data-driven/extensible | user-confirmed (Phase-10 reframe) | must-ship | new placement type / archetype addable as config, not code |
| REQ-F-104 | **Multi-swatch**: generate + export multiple recolors per object | user-confirmed (Phase 5) | must-ship | object shows multiple swatches in catalog |
| REQ-F-105 | Blender pipeline outputs **game-ready geometry** (GEOM + LODs + footprint/rig, correct scale/orient/origin) | inferred from REQ-F-101 | must-ship | imported mesh placeable + renders correctly in-game |
| REQ-NF-101 | **Bounded-parallel** item execution, configurable concurrency cap (~2–4), one active project | user-confirmed (Phase 4) | must-ship | N items generate concurrently up to cap |
| REQ-NF-102 | **Reconcile-and-resume** recovery: re-poll in-flight cloud job IDs on reopen; never lose accepted assets | user-confirmed (Phase 4) | must-ship | kill mid-run → reopen → resume/retry, no data loss |
| REQ-NF-103 | **Soft budget**: running cost estimate + warn-before-large-run; generation-mode→candidate-count mapping | user-confirmed (Phase 4) | must-ship | estimate shown; warning before large run |
| REQ-O-101 | **Test-install** to configured Sims 4 Mods folder + manual in-game check is part of the MVP loop | user-confirmed (Phase 1) | must-ship (anchor) | one-click install; item verified in-game |
| REQ-S-101 | Cloud API keys stored as **local secrets** (OS keychain / encrypted config), never plaintext in project | inferred (production-grade) | must-ship | keys not in project files/logs |
| REQ-I-101 | **UI↔pipeline IPC contract** as a versioned, mockable boundary (process/transport TBD by research) | inferred (Phase 1) | must-ship | UI runs against mock + real over same contract |
| REQ-D-101 | **App-managed local Postgres** (pgvector + JSONB + Alembic migrations) for relational/state + **artifacts as files on disk**; stable on-disk layout (project/item/candidate) | inferred (production-grade) + user (Phase 12) | must-ship | older project opens after schema bump; concurrent reads/writes ok |
| REQ-T-101 | Every pipeline op has a **mock adapter** producing realistic statuses/artifacts/failures | explicit — PRD PIPE-002 §13.2 | must-ship | full UI flow runs on mocks |
| REQ-O-102 | **Fail-open observability**: a LangSmith outage/offline must never block or fail a generation run | user-confirmed (Phase 12) | must-ship | run completes with LangSmith unreachable |
| REQ-I-102 | **LLM abstraction with two providers** (Claude direct + OpenRouter); default Claude class; keys in keychain | user-confirmed (Phase 12) | must-ship | swap provider/model via config; no key in logs |
| REQ-O-103 | **App-bundled binaries lifecycle-managed**: Postgres + Python sidecar + Blender detect (start/health/restart/stop) | inferred (production-grade) | must-ship | clean startup/shutdown; no orphan processes/ports |

### NFR budgets (numbers from PRD/user only)
- `locked decision` **No latency/throughput SLO numbers** stated — PRD says no real-time needed; the binding
  NFRs are **responsive UI during long jobs**, **stage progress visible**, **cancellable/skippable jobs**
  (PRD §22.5). 3D/mesh stages may be slow but must not freeze UI.
- `locked decision` **No cost ceiling** — surface running estimates per run; no hard cap (user, Phase 7).
- `locked decision` **Durability:** save intermediate state frequently; accepted assets never lost (§22.6 +
  REQ-NF-102).

---

## Phase 7 — Constraints, Evaluation, Timebox

### Constraints
- `locked decision` **Timebox:** none — **correctness-first**, no calendar pressure; sequence behind
  de-risking spikes. (Removes the main pressure to cut the full-fidelity scope.)
- `locked decision` **Team:** effectively solo product owner + the coding-agent team (this planning chain →
  `/tdd`). No multi-dev coordination constraints.
- `locked decision` **Platform:** Apple Silicon Mac (48 GB), macOS, local-first. Blender runs locally.
- `locked decision` **Compute:** cloud-first image-to-3D (WaveSpeed/Replicate/fal/…); local Mac fallback iff a
  capable model exists. `research required`.
- `proposed recommendation` **Required tech:** Python for the pipeline (LangGraph-class orchestration, `bpy`,
  image-to-3D clients are Python-native) — effectively forced; **confirm in Phase 11/12**.
- `open question`/`research required` **UI shell + UI↔pipeline process model:** undecided by user choice →
  research decides (Electron / Tauri / Python-native; sidecar-RPC vs in-process). Phase 10–11.
- `locked decision` **Forbidden / out:** no auth/accounts/multi-user; no CAS/animation/arbitrary mods; no
  marketplace/collaboration; broad cross-platform packaging deferred.
- `proposed recommendation` **Sims tooling:** prefer scripting an existing DBPF/packaging path over a
  from-scratch writer if a viable, Mac-runnable one exists — `research required` (most CC tooling is
  Windows/.NET; Mac viability is the open risk).

### Evaluation Criteria (what "good" is judged against)
- The **Y2K anchor scenario** runs end-to-end with ≥1 functional upgrade (PRD §6.2) — primary acceptance.
- **AC-001…018** + vertical-slice AC + UI AC all pass (PRD §26).
- **In-game test-install** confirms real placeability/behavior (the hard, honest bar this project chose).
- **Eval harnesses** (EVAL-001…009) runnable, incl. the image-to-3D **bakeoff** and **Blender** comparison.
- **Observability** present from day one (traces, lineage, review events).
- **Disqualifying:** content that won't load/place in-game; an unobservable pipeline; a UI that blocks on
  jobs; collapsing item-level state into one global flag; hard-coding a single 3D provider or Blender method.

---

## Phase 8 — Scope Inferences (posture: production-grade)

| Inference | Why it matters | Classification | Architecture impact |
|---|---|---|---|
| **Sims DBPF/GEOM export is a first-class subsystem**, not a final step | "real & placeable for all" makes it the dominant build | must-handle | dedicated export module + DonorMapping registry + GEOM/LOD/catalog/thumbnail writers; own spike |
| **EA tuning-clone subsystem** (registry-driven, "as many as feasible") | working in-game behavior via donor-tuning clone + retarget; open ceiling | must-handle | generic overlay engine driven by a data-driven archetype registry (not N hard-coded paths); own spike |
| **Open registries** (placement-type + functional-archetype) | user must never be boxed into a fixed item set | must-handle (user choice) | `Archetype`/`PlacementType`/`DonorMapping` are data-driven registries with validation, not enums; new entries are config + donor + test |
| **Game-ready geometry feasibility** from generated meshes | LODs/footprint/rig/scale may exceed automated Blender | research required | Blender spike must prove (or set manual-fallback hook) |
| **UI↔pipeline IPC contract + process supervision** | Python pipeline + desktop UI = a real boundary + a child process to manage | must-handle | versioned RPC schema, mock/real parity, sidecar lifecycle (start/health/restart) |
| **Provider/secrets/config layer** | cloud-first → keys, endpoints, rate-limits, retries, cost metering | production-hardening | adapter config + keychain secrets + retry/backoff + cost capture in traces |
| **Job/run engine distinct from the graph** | bounded-parallel, cancel, resume, reconcile cloud jobs | must-handle | durable run/step store + scheduler + reconciliation on startup |
| **Local store schema versioning + migration** | long-lived projects survive code changes | production-hardening | versioned project schema + migration path + backup-by-copy |
| **Artifact storage layout + GC** | many large mesh/image artifacts accumulate per project | production-hardening | deterministic by-project/item/candidate layout; retention/cleanup = deferred-but-flagged |
| **Structured error taxonomy + actionable messages** | creator-friendly failures + maintainer detail | must-handle | error types per stage; creator vs advanced surfacing |
| **Observability/eval scaffolding from day one** | pipeline is probabilistic/multimodal | production-hardening (PRD-mandated) | tracing + eval harness skeletons in Phase 0 of the build |
| **Mock-first parity contracts** | UI/pipeline parallel build | must-handle | every op has mock+real behind identical interface |
| **Cost estimation model** | "show estimates, no ceiling" still needs per-op cost data | must-handle | per-adapter cost metadata + run rollup in UI |
| **Multi-swatch generation + export** | recolors in MVP | must-handle (user choice) | swatch/texture worker + multi-preset DBPF + swatch UI |
| **Mac-side Sims tooling viability** | most packaging tooling is Windows/.NET | research required | Phase-10 research; may force custom writer or a cross-platform lib |
| Distribution/installers/code-signing/auto-update | only "a few known users" now | deferred (flagged) | keep build packaging simple; design so it can be added |
| Hard cost caps, artifact GC, manual-Blender-fallback UI | nice but not load-bearing for first correct build | deferred (flagged) | leave seams; don't build yet |

---

## Phase 9 — Assumptions and Open Questions

### Assumptions (category · why it matters · validation path · fallback)
| ID | Assumption | Category | Why it matters | Validation | Fallback |
|---|---|---|---|---|---|
| A1 | Cloud image-to-3D meshes can become game-ready after Blender cleanup | feasibility | core pipeline viability | image-to-3D **bakeoff** + Blender spike | better concept images; more cleanup; narrow archetypes |
| A2 | A **Mac-runnable path to write valid DBPF** packages exists (lib/tool/custom) | feasibility | the export gate; **most dangerous** | research R-003 + **export spike** | Windows helper/VM; custom DBPF writer; @s4tk (JS) |
| A3 | Cloning EA donor **tuning** yields working behavior for all 4 archetypes | feasibility | "real functional for all 4" | **functional spike** on 1 archetype | reduce archetype count; behavior-stub fallback |
| A4 | Automated Blender can produce LODs/footprint/rig (game-ready geometry) | feasibility | placeability | Blender spike | manual-fallback hook; decor-only first |
| A5 | User installs Sims 4 on the Mac for the **test-install loop** | process | makes "playable" verifiable | do it before anchor verification | structure-only verification + flag risk |
| A6 | LangGraph-class orchestration covers durable/resumable/HITL/**reconcile** locally | tech | run-engine backbone | research R-005 | custom lightweight graph runner |
| A7 | A **self-hostable local** observability platform exists | tech | day-one observability w/o SaaS | research R-007 | custom OTel/JSON trace store |
| A8 | Python pipeline + desktop UI is **packageable on macOS** for a few users | tech | distribution to known users | research R-006 | run-from-source dev setup |
| A9 | Cloud costs stay tolerable under "show estimates, no ceiling" | budget | sustainability | cost capture in traces | add soft caps later (deferred seam) |
| A10 | Most CC tooling being Windows/.NET won't block a Mac-first build | tech | Mac viability of export | research R-003 | cross-platform lib or helper process |

**Most dangerous (need fallback architecture):** A2, A3, A4, A1 — all converge on the **Sims export +
geometry + tuning** half of the system. Architecture must keep these behind adapters/spikes and design the
export + Blender + functional subsystems so a fallback (helper process, manual hook, reduced scope) slots in
without rework.

### Open Questions (best guess · when answered · status)
| ID | Question | Best guess | When | Status |
|---|---|---|---|---|
| OQ1 | UI shell + IPC transport | Electron/Tauri + Python sidecar over local RPC | Phase 11–12 (research R-006) | research running |
| OQ2 | Primary image-to-3D model/provider + bakeoff winner | a hosted TRELLIS/Hunyuan3D-class model | research R-001 + spike | research running |
| OQ3 | **DBPF export foundation** (lib vs tool vs custom) | @s4tk (JS) or a python DBPF lib; else custom | research R-003 + spike — **before export build** | research running |
| OQ4 | Blender strategy (deterministic / MCP / hybrid) | hybrid: deterministic core + agentic repair | Blender spike (BLEND-001) | pending spike |
| OQ5 | Orchestration framework | LangGraph | research R-005 + Phase 12 | research running |
| OQ6 | Observability platform | Langfuse (self-host) or local OTel | research R-007 + Phase 12 | research running |
| OQ7 | Concept image model | FLUX-class via cloud provider | research R-009 | research running |
| OQ8 | Per-archetype functional behavior feasibility | light/mirror easiest; audio/moodlet harder | functional spike | pending spike |
| OQ9 | Eval framework | pytest-custom + LLM-judge, optional promptfoo | research R-010 | research running |
| OQ10 | Final local-vs-cloud call for 3D | cloud-first confirmed; local fallback TBD | research R-002 | research running |
| OQ11 | Cross-platform (Windows) support beyond Mac | Mac-first MVP; Windows deferred | Phase 12 | open |

**Discipline:** none of these are silently resolved. The research workflow answers OQ1/2/3/5/6/7/9/10; the
spikes answer OQ4/8 and de-risk A1–A4; OQ11 is an explicit deferral.

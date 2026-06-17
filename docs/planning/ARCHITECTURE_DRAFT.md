# AI Sims Creator — Architecture (DRAFT)

> **Status:** First-draft canonical architecture spec — **build posture: production-grade** (narrow-but-open
> product surface). A *rough draft* for adversarial finalization by `/arch-finalize` (Brain 2). Not the
> binding contract yet.
>
> **Audience:** Project owner, technical reviewers, future Claude Code sessions, `/arch-finalize`, `/tasks-gen`.
>
> **Primary implementation constraint:** solo owner + coding-agent team; **no hard timebox (correctness-first)**;
> Apple-Silicon Mac (48 GB), macOS, local-first; cloud-first for image gen + image-to-3D.
>
> **Companion docs (read together):** `PRESEARCH.md`, `RESEARCH.md`, `DECISIONS.md` (ADR-001…014),
> `DATA_MODEL.md`, `USER_FLOWS.md`, `RISKS.md`, `DIAGRAM_PLAN.md`, `CLAUDE_CODE_HANDOFF.md`. Source PRD: `PRD.md`.
>
> **Build contract:** Treat this as the first-draft source of truth. `/arch-finalize` performs a second-pass
> gap audit, confirms load-bearing changes with the human, finalizes this into the binding `ARCHITECTURE.md`,
> and only then `/tasks-gen` produces `IMPLEMENTATION_PLAN.md`. Tasks bind to the `§<N>` anchors here.

---

## 1. Executive Summary  {#sec-1}
AI Sims Creator is a **local-first desktop studio** that turns a natural-language prompt into **installable,
in-game-placeable Sims 4 Build/Buy custom content**, through a **staged, observable, resumable, graph-
orchestrated pipeline**: *prompt → collection plan + style bible → concept image → image-to-3D mesh → mesh
QA → Blender cleanup/game-ready GEOM → Sims archetype map → optional functional overlay (EA tuning-clone) →
validation → DBPF export → test-install*. The product surface is a deliberately **narrow but open** MVP:
decorative generation is unlimited; placement-types and functional behaviors are **extensible registries**
seeded with a proven set. Engineering is **production-grade**: observability, evals, failure/retry paths,
human review gates, and durable resumability are in-scope from day one.

**Shape of the system:** an **Electron UI** (thin, reconnectable observer) over a **Python pipeline sidecar**
(durable job owner) running **LangGraph** with a **Postgres** checkpointer, which shells out to two subprocess
workers — **Blender (CLI)** for mesh/GEOM and a **Node `@s4tk` worker** for DBPF packaging — and calls cloud
**provider adapters** (image gen, image-to-3D, LLM) that are async-submit/poll and reconcilable after a crash.
Observability is **LangSmith** (fail-open). The two highest-risk subsystems (Sims **DBPF/GEOM export** and EA
**tuning-clone**) are sequenced behind **de-risking spikes first**.

## 1A. Goals & Non-Goals  {#sec-1a}
**Goals:** (G1) prompt→installable Sims 4 Build/Buy collection; (G2) real, in-game-placeable output for *all*
exported items; (G3) extensible functional behaviors ("as many as feasible"); (G4) full creator UI (11 screens)
+ dev panel; (G5) decoupled UI/pipeline via mock+real adapters; (G6) observability + 9 eval harnesses from the
start; (G7) resumable, recoverable, cost-aware generation.
**Non-Goals:** CAS / animation / arbitrary **novel scripted gameplay** (feasibility wall); multi-user/accounts/
collaboration; marketplace; guaranteed any-prompt→any-object; broad cross-platform packaging (MVP = Mac-first).

## 2. Product Definition and Scope  {#sec-2}
See `PRESEARCH.md` §Phase 0–1. **Posture:** production-grade engineering on a constrained-but-open surface.
**In-scope:** the full anchor flow (Y2K set) end-to-end + ≥1 functional archetype working in-game, verified by
**test-install**; decorative generation open for any prop; multi-swatch; bounded-parallel generation; soft
cost budget. **Deferred (flagged):** installers/code-signing/auto-update, broad Windows validation, hard cost
caps, artifact GC, manual-Blender-fallback UI, novel gameplay scripting.

## 3. Locked Architecture Decisions  {#sec-3}
Authoritative log: `DECISIONS.md` (ADR-001…014, all Locked). Summary:
| # | Decision |
|---|---|
| 01 | **Electron** shell + **Python/FastAPI sidecar** (localhost HTTP + SSE + cancel); Blender & @s4tk subprocess workers |
| 02 | **LangGraph 1.x** + **Postgres** checkpointer; app-owned startup reconciler + single-writer lock |
| 03 | Image-to-3D = provider abstraction; **co-primary Hunyuan3D-2.x + Tripo3D v2.5** (bakeoff decides); fal + WaveSpeed |
| 04 | Concept image = **model-agnostic adapter + bakeoff**; FLUX.2 [pro] seed default (not locked) |
| 05 | Sims export = **@s4tk Node worker** + **clone-a-donor**; donors from user's game install |
| 06 | Blender = **CLI-subprocess primary** (Blender 5.1.x/Py3.13), MCP excluded; **GEOM = first spike** |
| 07 | Observability = **LangSmith** (hosted); tracing **fail-open**; project data stays local |
| 08 | Evals = **LangSmith-native backbone + metric component layer** + pytest/pydantic/syrupy; DeepEval optional |
| 09 | Store = **app-managed local Postgres** (pgvector, JSONB, Alembic); artifacts as files; **keychain secrets** |
| 10 | Item types = **open registries** (placement-type + functional-archetype + donor mapping) |
| 11 | 3D = **cloud-first**; optional geometry-only local MPS fallback (feature-flagged) |
| 12 | **Production-grade**; spikes-first sequencing |
| 13 | **Mac-first** dev/test; architecture cross-platform-capable; Windows validation deferred |
| 14 | LLM = abstracted; **Claude direct + OpenRouter**; default Claude class; API-key auth (subscription = research) |

## 4. System Overview  {#sec-4}
Four runtimes + cloud + external tools:
- **UI process — Electron (Node + web UI).** 11 creator screens + dev panel. Thin observer: issues REST
  commands to the sidecar, subscribes to SSE for progress/logs, sends cancel. Holds **no durable pipeline state**.
- **Pipeline sidecar — Python (FastAPI).** The **durable job owner**: runs LangGraph, owns Postgres + the
  artifact store, supervises subprocess workers, calls cloud adapters, emits LangSmith traces. Survives UI
  crashes; UI reconnects and replays over SSE.
- **Mesh worker — Blender 5.1.x CLI** (`blender --background --factory-startup --python`). Cleanup, game-ready
  geometry (LODs/footprint/normals/UVs), preview render, GEOM export, and the render-bridge for evals.
- **Export worker — Node `@s4tk`.** DBPF clone-and-replace packaging (the PACKAGER; consumes GEOM bytes).
- **Cloud providers** (adapters): concept-image gen, image-to-3D, LLM. All async submit+poll/webhook.
- **External tools/data:** local Blender install (detected/bundled), the user's **Sims 4 install** (donor
  packages + test-install Mods folder), **LangSmith** (cloud observability).

Data plane: artifacts (images, meshes, packages) live as **files on disk**, organized by project/item/candidate;
**Postgres** holds metadata, state, registries, lineage, and the LangGraph checkpoint. **OS keychain** holds
provider/LLM API keys.

## 4A. Subsystem Dependency DAG & Parallelization Seams  {#sec-4a}
**Import-direction rule:** UI → (IPC contract) → Sidecar API → Pipeline/Graph → Stages → Adapters/Workers →
Stores. **Lower layers MUST NOT import upper layers.** The **shared contracts package** (IPC schema + domain
types + provider interfaces) is imported by everyone and **frozen first**.

**Frozen-first contracts (the integration seams):**
1. **IPC contract** (REST command schema + SSE event schema + cancel) — UI ⇄ Sidecar.
2. **Domain types/schemas** (Project, ItemSpec, candidates, AssetVariant, Swatch, FunctionalOverlay, runs/
   steps, validation, export, registries) — pydantic (Python) ↔ TS types (UI/Node), kept in sync.
3. **Provider interfaces** (`ImageGenProvider`, `Image3DProvider`, `LLMProvider`) — `submit/poll/fetch`.
4. **Worker contracts** — `BlenderJob` (in: mesh/params; out: cleaned GEOM/preview/report) and
   `ExportJob` (in: donor + GEOM + textures + tuning edits + TGI keys; out: `.package` + report).
5. **Registry schemas** — PlacementType, FunctionalArchetype, DonorMapping.

**Independent parallel build tracks** (after contracts freeze):
- **Track A — UI** (all 11 screens + dev panel) against **mock adapters/sidecar**.
- **Track B — Pipeline core** (LangGraph graph, job/run engine, reconciler, Postgres store, mock stages).
- **Track C — Sims export** (@s4tk worker + donor registry) — *spike-gated*.
- **Track D — Mesh/Blender** (cleanup + game-ready GEOM + render) — *spike-gated*.
- **Track E — Providers** (image-gen, image-to-3D, LLM adapters + bakeoffs).
- **Track F — Observability + evals** (LangSmith wiring + metric component layer).
Integration owner: the **sidecar** is where A↔B↔(C,D,E) meet; the IPC + provider + worker contracts are the
merge points.

## 5. Domain Model  {#sec-5}
Full model in `DATA_MODEL.md` (16 entities, 6 state machines, 10 invariants). Key points: one **ItemSpec**
identity carries decor + (optional) functional overlay ("one asset, multiple outputs"); candidate→accepted
funnel with **lineage** (mesh←concept←spec←plan←prompt); **open registries** (PlacementType,
FunctionalArchetype, DonorMapping) replace fixed enums; **multi-swatch** per AssetVariant. State machines:
project; 13-state item; 8-state run/step; concept; mesh; overlay; export.

## 6. Core Module / Service / Contract Architecture  {#sec-6}
**6.1 IPC layer** — FastAPI on a dynamically-chosen free localhost port; REST for commands (create project,
start run, approve gate, include/exclude, edit, export, test-install, rerun-step), **SSE** for progress/log/
state streams (resumable: `Last-Event-ID`), `DELETE /jobs/{id}` (or WS) for cooperative cancel. Contract is
versioned + mockable (REQ-I-101); UI runs identically against mock and real.

**6.2 Job/run engine** — distinct from the graph (ADR-002). Schedules items **bounded-parallel** (configurable
cap ~2–4, one active project), persists run/step state in Postgres, streams progress, enforces tool-call
boundaries, captures cost/latency. **Startup reconciler** enumerates incomplete threads and re-polls in-flight
cloud jobs by stored `provider+job_id`; **single-writer lock** prevents double-resume.

**6.3 LangGraph pipeline** — `StateGraph`, one node/subgraph per stage; typed State carries artifacts +
provider job_ids + status. Cloud steps = **two-phase nodes** (`@task` idempotent submit → store job_id → poll/
reconcile). Approval gates = `interrupt()` / `Command(resume)`. `durability='sync'` for cloud/long stages.

**6.4 Provider adapters** (registries + bakeoff) — `ImageGenProvider`, `Image3DProvider`, `LLMProvider`, each
`submit(input,params)→job_id · poll(job_id)→{status,progress,urls} · fetch(urls)→local artifacts`. Mock + real
behind one interface (PIPE-002/003). Bakeoffs (EVAL-002/003) select models empirically. Cost metadata per op.

**6.5 Worker subsystems** — **Blender worker** (CLI subprocess; cleanup + game-ready GEOM + preview + render
bridge) and **Export worker** (Node @s4tk; clone-a-donor DBPF). Both behind worker contracts (§4A), with
timeouts, structured errors, process-tree teardown.

**6.6 Registries** — data-driven PlacementType / FunctionalArchetype / DonorMapping with validation; adding an
entry is config (+ donor + test), not code (ADR-010).

**6.7 Workers/agents (LLM)** — Collection Planner, Style Bible, Concept-Prompt, Archetype-Mapper, Functional-
Overlay Planner, Repair — each calls the `LLMProvider`; structured outputs validated before writing state.

**6.8 Supervisor** — lifecycle for the three bundled binaries (Postgres, Python sidecar, Blender-detect):
free-port selection, spawn, `/health` poll, supervised restart w/ backoff, clean process-tree teardown (REQ-O-103).

## 7. Data and State Model  {#sec-7}
**Source of truth = app-managed Postgres** (relational/state/registries/lineage + LangGraph checkpoint, ADR-09)
+ **filesystem artifacts** (by project/item/candidate). pgvector reserved for preference/similarity (OBS-004/
EVAL-009). JSONB for flexible spec/config blobs. **Alembic** migrations; backup = copy folder + `pg_dump`.
Invariants + state machines: `DATA_MODEL.md`. Accepted assets immutable without confirmation. Secrets:
**OS keychain** (encrypted-file fallback), never in DB/logs/traces.

## 8. User Flows  {#sec-8}
Full set (A–F creator + G–K system/admin) with success/failure/recovery/data-touched + the
**bounded-parallel / reconcile-resume / soft-budget / scoped-repair** behaviors: `USER_FLOWS.md`. Five human
review gates: plan · concept · mesh · overlay · export. Recovery: reconcile-and-resume on reopen. Coverage
table proves every in-scope requirement maps to a flow.

## 9. Integration Architecture  {#sec-9}
- **Image gen** (concept) — model-agnostic adapter (ADR-04); seed FLUX.2 [pro] (transparent_bg → silhouette);
  WaveSpeed default, Replicate/fal/OpenRouter alternates; rembg fallback; pinned seed.
- **Image-to-3D** (ADR-03) — co-primary Hunyuan3D-2.x + Tripo3D v2.5 via fal (one API) + WaveSpeed; async
  submit/poll/webhook; persist job_id; ⚠️ Tripo 24h URL expiry → download promptly. Output GLB+PBR.
- **LLM** (ADR-14) — Claude direct + OpenRouter behind `LLMProvider`; structured outputs; keychain keys.
- **Blender** — local CLI subprocess (GPL boundary; subprocess IPC ≠ derivative work). Detect/bundle; pinned
  5.1.x/Py3.13.
- **@s4tk** — Node subprocess; reads donor `.package` from the user's game install, writes DBPF.
- **LangSmith** — env-var/callback tracing; **fail-open**; artifact *references* only (binaries stay local).
- **Sims 4 install** — donor source + **test-install Mods folder** target (configurable path).

## 10. Automation / Background Jobs  {#sec-10}
Pipeline runs (System Flow G), scoped repair loops (H), crash/abandonment **reconcile-and-resume** (I),
dependency-failure handling with retry/backoff + alternate adapter (J), maintainer/dev-panel ops (K). All
durable in Postgres; all traced; all fail-isolated per item.

## 11. Frontend Architecture  {#sec-11}
Electron + web UI (framework TBD by impl — React-class). 11 screens (UI-001…011) + dev panel; **Creator vs
Advanced mode** gate. State = server-driven via SSE (sidecar is source of truth); optimistic local UI only for
edits. Long jobs never block UI; progress per item+stage; cancel/skip where feasible. Runs against **mock
adapters** first (Track A). Cost estimate surfaced; soft-budget warning before large runs.

## 12. Backend / API / Pipeline Strategy  {#sec-12}
Python sidecar = FastAPI (IPC) + LangGraph (orchestration) + job/run engine + adapters + worker supervisors +
Postgres repository layer + OTel/LangSmith instrumentation. Repository pattern abstracts the DB engine (so the
SQLite fallback in ADR-09 is a contained swap). Stateless-compute vs durable-state cleanly separated.

## 13. Shared Package / Config Strategy  {#sec-13}
**Shared contracts package** (frozen first, §4A): domain types/schemas as the single source of truth, generated
or hand-synced to TS for UI/Node. Config: provider/model registry, generation-mode→candidate-count map, donor
registry, feature flags (local-3D fallback), paths (artifact root, Sims Mods folder). Secrets via keychain.

## 14. Testing Strategy  {#sec-14}
**Evals (ADR-08):** LangSmith-native backbone (datasets, `evaluate_comparative` bakeoffs, annotation queues,
`@pytest.mark.langsmith` CI) + **metric component layer** (trimesh/Open3D/torchmetrics/IQA + **Blender render
bridge**) + pytest/pydantic/syrupy. 9 harnesses EVAL-001…009 map to the stages. Caveats: reference-mesh metrics
only on benchmark sets; aesthetic/IQA = directional, never hard gates; pin judge model + weights for CI
determinism. **Unit/integration:** mock adapters give full-flow tests without cloud; DBPF round-trip +
**test-install** gate in validation; contract tests on the IPC + worker + provider interfaces.

## 15. Security and Risk  {#sec-15}
Full register: `RISKS.md`. **Trust boundaries:** (a) UI↔sidecar localhost IPC (validate all commands;
sidecar is sole writer); (b) sidecar↔cloud providers (API keys from keychain; validate/limit responses;
cost/rate-limit handling; nothing trusts provider output without validation); (c) sidecar↔LangSmith (fail-open;
no secrets/PII in traces; artifact refs only); (d) sidecar↔Blender/@s4tk subprocess (validate
inputs/outputs; timeouts; MCP-style/agent outputs pass deterministic validation before state writes);
(e) export↔user's game install (read donors, write Mods folder — never overwrite without confirm).
**Top risks (see RISKS.md):** R1 GEOM/export feasibility on Mac (headless GEOM unproven) · R2 functional
tuning-clone breadth · R3 AI-mesh→game-ready geometry · R4 macOS packaging/notarization (sidecar + Postgres
+ Blender) · R5 cloud cost/rate-limits · R6 LangSmith data-egress + offline · R7 EA-patch format drift.

## 16. Deployment Strategy  {#sec-16}
**MVP = shareable build for a few known users** (light packaging). macOS app bundle = Electron + **deep-signed,
notarized** PyInstaller (or python-build-standalone) sidecar + **bundled Postgres** + Blender (detect-or-bundle,
GPL source link). CI automates sign/notarize/staple early (high-risk — verify end-to-end on a clean Apple
Silicon machine). Local data dir for Postgres + artifacts; configurable Sims Mods path. **Deferred:** installers/
auto-update/code-signing-for-public/Windows. **Anchor "demo" = the Y2K end-to-end run + in-game test-install.**

## 17. Alternatives Considered  {#sec-17}
Per-decision options/tradeoffs in `DECISIONS.md` + `RESEARCH.md`: Tauri/PySide6 (vs Electron); Burr/Temporal
(vs LangGraph); custom DBPF writer / Windows-helper-VM (vs @s4tk); bpy-module / MCP (vs Blender CLI);
Phoenix/Langfuse (vs LangSmith); DeepEval/Inspect AI (vs LangSmith-native evals); SQLite (vs Postgres);
fixed lists (vs open registries). Each has a recorded fallback + invalidation condition.

## 18. Scope Boundaries and Deferred Work  {#sec-18}
**Open ceiling:** decorative breadth unlimited; functional archetypes "as many as feasible." **Out-of-scope
frontier:** novel scripted gameplay. **Deferred (flagged, seams left):** installers/code-signing/auto-update,
Windows validation, hard cost caps, artifact GC, manual-Blender-fallback UI, cloud-Blender, local-3D beyond
geometry-only. **Spikes-first (must precede breadth):** S1 GEOM/DBPF export, S2 image-to-3D bakeoff, S3
functional tuning-clone (one archetype).

## 19. Diagrams  {#sec-19}
Planned in `DIAGRAM_PLAN.md`: full-system map; pipeline lifecycle sequence; item state machine; domain model;
reconcile-resume flow; trust-boundary diagram; export clone-a-donor flow; eval harness map.

## 20. Repo Scaffold  {#sec-20}
Monorepo (proposed):
```
apps/desktop/            # Electron shell + web UI (Track A)
services/pipeline/       # Python sidecar: FastAPI, LangGraph, engine, adapters, repos (Tracks B,E)
  pipeline/graph/        #   stage nodes + two-phase cloud nodes
  pipeline/adapters/     #   imagegen/, image3d/, llm/ (mock+real)
  pipeline/engine/       #   job/run engine, reconciler, supervisor
  pipeline/registries/   #   placement_type, functional_archetype, donor_mapping
  pipeline/store/        #   Postgres repos, Alembic migrations
workers/blender/         # Python bpy scripts run via Blender CLI (Track D)
workers/export/          # Node @s4tk DBPF clone-a-donor worker (Track C)
packages/contracts/      # IPC schema + domain types (py⇄ts) + provider/worker interfaces (frozen first)
evals/                   # LangSmith datasets + metric component layer + harnesses (Track F)
  evals/metrics/         #   trimesh/open3d/torchmetrics/iqa wrappers + render bridge
docs/planning/           # this planning package
```

## 21. Decision Summary Table  {#sec-21}
See §3 + `DECISIONS.md` (ADR-001…014, all Locked, each with fallback + invalidation).

## 22. Spec Anchor Index  {#sec-22}
`#sec-1` Exec summary · `#sec-1a` Goals/Non-goals · `#sec-2` Scope · `#sec-3` Locked decisions · `#sec-4`
System overview · `#sec-4a` Dependency DAG/parallel seams · `#sec-5` Domain model · `#sec-6` Core modules/
contracts · `#sec-7` Data/state · `#sec-8` User flows · `#sec-9` Integrations · `#sec-10` Automation · `#sec-11`
Frontend · `#sec-12` Backend/pipeline · `#sec-13` Shared/config · `#sec-14` Testing/evals · `#sec-15` Security/
risk · `#sec-16` Deployment · `#sec-17` Alternatives · `#sec-18` Scope/deferred · `#sec-19` Diagrams · `#sec-20`
Repo scaffold · `#sec-21` Decision summary · `#sec-23` Review instructions.

## 23. Claude Code Review Instructions  {#sec-23}
See `CLAUDE_CODE_HANDOFF.md`. In short: read all of `docs/planning/*` + PRD; **do not implement**; run the
gap audit against the **production-grade** posture; confirm load-bearing changes with the human; finalize into
binding `ARCHITECTURE.md`; only then `/tasks-gen` → `IMPLEMENTATION_PLAN.md`, with **spikes S1–S3 sequenced
first** and every task bound to a `#sec-` anchor.

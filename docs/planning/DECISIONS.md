# DECISIONS — AI Sims Creator (ADR log)

> Phase-11/12 artifact. ADR-style records for load-bearing architecture decisions, grounded in
> `RESEARCH.md` (R-001…010) + the Phase 0–9 interview. **Status convention:** `Proposed (lock pending)` until
> the user confirms in Phase 12; PRD-mandated items are `Locked`. Fallbacks + invalidation conditions are
> recorded so the design degrades gracefully. Brain 2 (`/arch-finalize`) adversarially re-checks these.
>
> **⟢ Finalize (Brain 2) updates applied:** ADR anchor refs resolve via `docs/gap-audits/anchor-remap.md`
> (draft `#sec` → binding `§`). Audit-driven corrections: ADR-002 (checkpointer ownership + verify), ADR-005
> (licensing), ADR-006 (MCP arm restored per PRD §15.4/§17.2), ADR-007 (contradiction removed). **Scope
> guardrails loosened (owner-confirmed):** PRD §27.18/§28.6 anti-overbuild guardrails deliberately overridden —
> first target = full-fidelity for all items + as-many-archetypes-as-feasible; spikes S1/S2/S3 remain
> *feasibility* gates (binding `ARCHITECTURE.md` §20). **Binding contract = repo-root `ARCHITECTURE.md`.**

## Locked-Decision Summary (Phase 12)
| # | Area | Decision | Status | Fallback |
|---|---|---|---|---|
| 01 | UI shell + process model | Electron shell + Python(FastAPI) sidecar (HTTP+SSE+cancel); Blender & @s4tk as subprocess workers | Locked | Tauri (same contract) → PySide6 (single-process) |
| 02 | Pipeline orchestration | LangGraph 1.x + **Postgres** checkpointer; app-owned reconciler + single-writer lock | Locked | Apache Burr; Temporal only if server justified |
| 03 | Image-to-3D | Provider abstraction; **co-primary Hunyuan3D-2.x + Tripo3D v2.5** (bakeoff decides); fal + WaveSpeed | Locked | flip model-id; Replicate; Rodin |
| 04 | Concept image | **Model-agnostic adapter + bakeoff** (registry); FLUX.2 [pro] = seed default, not locked | Locked (user) | any registry model + rembg; local FLUX.2 klein |
| 05 | Sims export/packaging | **@s4tk Node worker** (packager) + **clone-a-donor** + data-driven donor registry | Locked | custom ZLIB DBPF writer; loose-files + manual S4S finish |
| 06 | Blender stage | Hybrid: **CLI-subprocess primary** + bpy spike; Blender 5.1.x/Py3.13 pin; **MCP excluded**; GEOM = first spike | Locked | pinned-old-Blender GEOM microservice; custom GEOM writer; Windows helper VM |
| 07 | Observability | **LangSmith (hosted SaaS)** — native LangGraph; tracing fail-open; project data stays local | Locked (user) | Phoenix/Langfuse (local) if SaaS unwanted |
| 08 | Eval harness | **LangSmith-native backbone + metric component layer (trimesh/Open3D/torchmetrics/Blender-render) + pytest/pydantic/syrupy**; DeepEval optional | Locked (user) | DeepEval or Inspect AI as runner |
| 09 | App store + secrets | **App-managed local Postgres** (pgvector, Alembic), artifact files on disk, keychain secrets | Locked (user) | SQLite if packaging Postgres too heavy |
| 10 | Item-type model | **Open registries** (placement-type + functional-archetype + donor mapping) | Locked (user) | n/a (this IS the de-risk of fixed lists) |
| 11 | Local 3D fallback | Cloud-first; optional **geometry-only local MPS** (TRELLIS.2 port), feature-flagged | Locked | drop local; cloud-only |
| 12 | Build posture & scope | Production-grade; narrow-but-open surface; **spikes-first** sequencing | Locked (Phase 0) | n/a |
| 13 | Cross-platform | **Mac-first dev/test**; architecture cross-platform-capable; Windows validation deferred | Locked | n/a |
| 14 | LLM provider | Abstracted; **Claude direct + OpenRouter** (both); default Claude class; API-key auth (subscription=research) | Locked (user) | swap model/provider via abstraction |

---

## ADR-001 — UI shell + UI↔pipeline process model
**Status:** Locked — *user delegated this to research (Phase 7)*.
**Context:** Polished, observable, resumable desktop creator UI over a Python-heavy pipeline (LangGraph, image-to-3D HTTP clients, Blender, @s4tk); Mac-first; few users.
**Options:** Electron+Python sidecar (mature, deepest macOS packaging, no Rust; heavier) · Tauri+sidecar (lighter <10MB/<0.5s; Rust + less-mature sidecar lifecycle) · PySide6 (single-language, no IPC; non-web Qt UI).
**Decision:** **Electron shell + Python(FastAPI) sidecar on a dynamic localhost port; REST commands + SSE progress/logs + DELETE/WS cancel. Sidecar = durable resumable job owner; UI = thin reconnectable observer. Blender (CLI) and @s4tk (Node) run as subprocess workers the sidecar shells out to (Electron already bundles Node).**
**Rationale:** UI is the product (rich, web-first); pipeline is Python; SSE streams graph state and is trivially resumable; matches every other decision. **Tradeoff acknowledged:** macOS notarization of the PyInstaller sidecar + sidecar lifecycle (free-port, /health, supervised restart, process-tree kill) are real, high-effort infra — CI'd early.
**Fallback:** Tauri (identical sidecar contract → low migration) if Electron footprint hurts; **PySide6** (one process, one signing target) if notarization/lifecycle prove too fragile.
**Invalidation:** notarization repeatedly unsolvable for the sidecar; or footprint/UX demands force a lighter shell. **Related:** REQ-I-101, R-006. **Anchors:** §3, §4, §11.

## ADR-002 — Pipeline orchestration engine
**Status:** Locked.
**Context:** Stateful, resumable, human-gated, mock-or-real pipeline that must reconcile in-flight cloud jobs after an app restart, in-process on a desktop (no server).
**Options:** LangGraph 1.x (in-process, SQLite checkpointer, native HITL; reconcile not automatic) · Apache Burr (state machine, SQLite, local trace UI) · Temporal (true durable exec, needs server) · LlamaIndex Workflows+DBOS · custom runner.
**Decision:** **LangGraph 1.x + langgraph-checkpoint-postgres** (pinned together; aligns with ADR-009's Postgres store — one DB for app data + checkpoints). StateGraph one node/subgraph per stage; typed State carries artifacts + provider job_ids + status; one thread_id per run. Cloud steps = two-phase (`@task` submit + poll/reconcile node). Approval gates = `interrupt()`/`Command(resume)`. `durability='sync'` for cloud/long stages. **App owns the startup reconciler (enumerate incomplete threads → re-invoke) + a single-writer lock** (LangGraph has no watchdog/dup-prevention).
**Rationale:** Only option meeting every hard need in-process with zero infra; idempotent-submit + job-id-in-state is the reconcile spine.
**Fallback:** Apache Burr (stage funcs + reconcile pattern port over); Temporal if guaranteed durable execution later justifies a bundled server.
**Invalidation:** LangChain churn/coupling becomes blocking; replay/idempotency model fights cloud-reconcile. **Related:** REQ-NF-101/102, R-005. **Anchors:** binding §5, §6.
**⟢ Finalize note:** checkpointer = `langgraph-checkpoint-postgres` (one DB with §13) + **ownership partition** (checkpoint = in-flight graph *position* only; app repo owns Run/Step/candidate/variant rows). **Verify `langgraph-checkpoint-postgres` parity at build start** (R-005 validated only the SQLite saver); SQLite-saver-in-separate-file = fallback.

## ADR-003 — Image-to-3D provider + model
**Status:** Locked.
**Context:** Cloud-first single-image→3D; needs game-ready topology; must support a bakeoff + reconcile-resume.
**Options:** fal aggregator (one API → Tripo/Hunyuan3D/TRELLIS/Rodin/Meshy) · WaveSpeed (Hunyuan3D V3) · Replicate (cheap, community) · direct vendor APIs.
**Decision:** **`Image3DProvider` interface** (`submit→job_id` · `poll` · `fetch`). **Two co-primary defaults: Hunyuan3D-2.x and Tripo3D v2.5** (the bakeoff, EVAL-003, picks the winner per real Sims props); first adapter built on **fal** (one API fronting both + TRELLIS/Rodin/Meshy), with **WaveSpeed** as the second vendor (hosts Hunyuan3D v3 + FLUX, aligning with ADR-004). Persist provider+job_id in graph state; webhook where available, poll-on-resume fallback. ⚠️ handle Tripo's 24h URL expiry (download promptly; reconcile = re-download if not persisted).
**Rationale:** One adapter unlocks all models for the bakeoff; async shape fits reconcile-resume. **Hunyuan3D-2.x = best raw fidelity/PBR** (dense triangles, but our Blender decimate/remesh + LOD stage absorbs that); **Tripo v2.5 = cleanest native game (quad) topology, least cleanup**. Co-defaulting both lets the bakeoff decide on real assets rather than pre-committing.
**Fallback:** flip fal model-id → Hunyuan3D/TRELLIS; second vendor WaveSpeed; cost Replicate; premium Rodin; offline = local geometry-only (ADR-011).
**Invalidation:** bakeoff shows Tripo quad insufficient for Sims; fal availability/pricing degrades. **Related:** REQ-F-105, EVAL-003, R-001. **Anchors:** §6, §7.

## ADR-004 — Concept image generation
**Status:** Locked (user) — **model-agnostic adapter, NOT FLUX.2-locked.**
**Context:** Need clean, isolated, single-object concept images optimized as image-to-3D input.
**Decision:** **`ImageGenProvider` interface with a model registry + a concept-image BAKEOFF** (mirrors ADR-003 image-to-3D). No model lock-in: providers (WaveSpeed/Replicate/fal/OpenRouter) and models are swappable/testable behind one interface; a bakeoff (extend EVAL-002) compares models on silhouette cleanliness + downstream image-to-3D reconstruction quality. **FLUX.2 [pro] is the seed default candidate** (native `transparent_bg` RGBA → clean silhouette, skip rembg), with FLUX.2 dev, Z-Image Turbo, Imagen 4, etc. as registry entries. Fixed isolated-object prompt template + pinned seed (resumability) + 1024–1536px; emit N candidates + silhouette-quality score gate; rembg fallback for models lacking transparent_bg; optional multi-view.
**Rationale:** Same open-registry philosophy as everywhere else — pick the winner empirically per real assets, never pre-commit; transparent_bg is *a* differentiator FLUX.2 happens to lead today, not a reason to lock it.
**Fallback:** any registry model + rembg; local FLUX.2 klein via MLX offline.
**Invalidation:** a better isolated-object model emerges (just add to registry). **Related:** REQ-NF-103, REQ-F-106, EVAL-002, R-009. **Anchors:** §6.

## ADR-005 — Sims export / packaging
**Status:** Locked.
**Context:** Real, placeable-in-game DBPF for every item, Mac-runnable, clone-and-replace.
**Options:** @s4tk Node lib (mature, cross-platform read+writer; GEOM opaque) · custom DBPF writer · s4py (dormant) · S4S (GUI, no CLI).
**Decision:** **DBPF export = a Node worker on the @s4tk stack** (models/compression/hashing/images/xml-dom), vendor-pinned. **Clone-a-donor**: open donor `.package` → swap GEOM/textures/thumbnail/COBJ → keep OBJD-tuning/FTPT/RIG/SLOT for functional → re-serialize. **Hard split: MESH stage (→GEOM bytes, ADR-006) is separate from PACKAGE stage (s4tk embeds bytes).** Donors sourced from the **user's own game install** at runtime (licensing). DBPF round-trip + **test-install** gate in validation.
**Rationale:** Only mature cross-platform DBPF writer; runs native on Apple Silicon, no .NET/VM.
**Fallback:** custom ZLIB-only DBPF writer reusing s4tk encoders; worst case ship loose resources + one-click S4S project for manual finish.
**Invalidation:** s4tk abandoned + a needed resource type missing; EA patch breaks format. **Related:** REQ-F-101/103/104/106, R-003/004. **Anchors:** binding §9, §10.
**⟢ Finalize note (licensing):** clone-a-donor extracts EA donor resources from the **user's own game install** into shipped `.package` files — the standard, de-facto Sims-modding posture (S4S et al.). Confirmed **non-commercial, few-known-users** → recorded as a RISK + `research-required` (binding §10, §22), **not a blocker**. Revisit before any wider/public distribution. Atomic write + read-only donors + DBPF round-trip gate per binding §9.

## ADR-006 — Blender / geometry stage  *(highest residual risk)*
**Status:** Locked — **GEOM export approach is spike-gated.**
**Context:** Mesh cleanup + game-ready geometry (LODs/footprint/normals/UVs) + Sims GEOM export, headless on macOS.
**Options:** bpy-module in-process (deterministic, but headless GPU/crash limits) · CLI subprocess (isolation, full render, decouples Python version) · MCP (GUI-bound, nondeterministic → **excluded**).
**Decision:** **Hybrid, CLI-subprocess as the production execution path** (`blender --background --factory-startup --python`; GPL isolation, crash containment, decouples sidecar Python from Blender's 3.13, full render); **bpy-module for the spike A/B + fast iteration**. **Pin Blender 5.1.x + Python 3.13 + bpy 5.1.2, Apple-Silicon.** Blender stage owns the **game-ready gate** (rescale to donor bbox, floor origin, **normal recalc/transfer**, UV validation, meshgroup match, 3–4 LOD + shadow-LOD gen, per-tile poly budget ~2000 tris/tile LOD0). **GEOM export is its own vendored, version-pinned sub-dependency + validation step — and the FIRST spike**, because no maintained headless Blender-5 Sims-4 GEOM exporter is confirmed to exist.
**Rationale:** Reconciles R-006 (CLI for GPL/isolation) with R-008 (deterministic core); MCP can't be a reproducible stage executor.
**Fallback:** pinned-old-Blender GEOM microservice; **custom GEOM writer** (s4py/s4sdk refs); Windows helper VM for the mesh stage only.
**Invalidation:** spike finds no viable headless GEOM path → escalate to a fallback (added scope). **Related:** REQ-F-105, BLEND-001, EVAL-004, R-008. **Anchors:** binding §8, §9.
**⟢ Finalize note (MCP arm restored):** to honor PRD §15.4/§17.2 (3-way Blender spike; "must not reject MCP-driven Blender control prematurely"), the Blender spike (S1, EVAL-004) **includes a lightweight agentic-MCP-repair arm** — {CLI (default) vs bpy} × {deterministic-core vs deterministic+**MCP-repair** hybrid}; MCP is evaluated for judgment-heavy repair (PRD §15.6 hybrid), not pre-excluded from the comparison. CLI-subprocess remains the production default; outcome recorded (binding §8, §15).

## ADR-007 — Observability backend
**Status:** Locked (user) — **LangSmith (hosted SaaS, cloud tier).**
**Context:** Multimodal artifact lineage (concept images, meshes, DBPF previews), cost/latency, review events, integrates with LangGraph.
**Decision (final):** **LangSmith hosted** — native LangGraph tracing via env-var/callback, zero local infra, best LangGraph DX. **Project data stays local (ADR-009)**; only traces/metadata + artifact *references* go to LangChain's cloud (large binaries stay on the local filesystem). Wrap instrumentation behind a thin tracing seam so Phoenix/Langfuse (local) stay low-cost swaps. ⚠️ **Accept + design for:** SaaS data-egress (prompts/traces leave the machine), recurring cost, and **fail-open tracing** (a LangSmith outage/offline must NEVER block or fail a generation run). Capture user accept/reject as LangSmith feedback/runs.
**Below: the options considered (record).**
**Options (re-opened to include LangSmith per user):**
- **LangSmith (HOSTED SaaS)** — *tightest LangGraph integration* (same ecosystem, native callback), **zero infra**, free Developer tier + Plus ($39/user/mo). **But:** SaaS — prompts/traces/(possibly artifacts) **leave the machine** to LangChain's cloud (conflicts with local-first), recurring cost, multimodal artifact lineage weaker than Langfuse. *Self-host is Enterprise-license-gated ($950+/mo) → not viable; "LangSmith" here means the cloud tier.*
- **Arize Phoenix** — single container / `pip + phoenix serve`, OTel-native, auto-instruments LangGraph, **lightest local**, fully private; weaker durable-artifact lineage.
- **Langfuse v4** — native OTel + **first-class multimodal artifact lineage** to MinIO; 6-container Docker (heavy to ship); fully local/private.
- **Phoenix default + Langfuse-optional** — ship Phoenix; OTel keeps Langfuse a drop-in for deep lineage when wanted.
- custom OTel (build everything) — last resort.
**Backend-portability note (record — NOT a competing decision; the binding Decision above is LangSmith):** OTel instrumentation keeps the backend swappable. The fork weighed was **LangSmith hosted = lowest-effort + best LangGraph DX, but non-local + recurring cost** vs Phoenix/Langfuse = local-first/private. Switching backends is low-cost on the common OTel/OpenInference path — but per ADR-008 the *eval-backbone* portability is a **separate** seam (abandoning LangSmith also costs an eval-runner migration). *(LangSmith's native integration is via LangChain callbacks, slightly tighter than generic OTLP.)*
**Fallback:** any other backend; raw OTel + Tempo/Jaeger last resort. **Related:** OBS-001…005, R-007. **Anchors:** §12.

## ADR-008 — Eval harness framework  *(REVISED after the LangSmith lock + eval-deepdive)*
**Status:** Locked (user) — revised from the first-pass DeepEval-primary.
**Context:** 9 harnesses (dev/CI only, not shipped); multimodal + mesh-heavy; vendor-neutral judge; **LangSmith + LangGraph already locked**.
**Decisive finding:** **NO eval framework has native 3D-mesh metrics** — mesh eval is custom Python in *every* option. So framework choice is about *datasets / CI gating / pairwise / human-pref / trajectory*, **not metrics**; the metrics are a separate component layer that must be built regardless.
**Decision (revised):**
1. **Backbone / system-of-record = LangSmith-native evals** — versioned **datasets**, **experiments**, `evaluate()`/**`evaluate_comparative()`** (turnkey image-to-3D **bakeoff**), **annotation queues** (human-preference), **`@pytest.mark.langsmith`** CI gating, **agentevals** trajectory evaluators. Reuses the locked LangSmith+LangGraph (graphs pass straight into `evaluate()`); one-click trace→dataset loop. Vendor-neutral **judge = Claude/OpenRouter inside plain-Python evaluators** (no OpenAI requirement). Offline/CI: `LANGSMITH_TEST_TRACKING=false` for dry-runs, `LANGSMITH_TEST_CACHE` to cut judge cost.
2. **Metric component layer (framework-agnostic — the real engineering):** **mesh** = `trimesh` (watertight/winding/normals/euler/nondegenerate + Sims per-tile poly budget, LOD presence, UV/bbox sanity) + **Open3D 0.19 `compute_metrics`** (Chamfer/Hausdorff/F-score, ARM64 wheels) + PyMeshLab (repair/sampling); **image** = `torchmetrics` 1.9 (LPIPS/SSIM/PSNR/CLIPScore) + IQA-PyTorch (MUSIQ/TOPIQ/aesthetic) + open_clip; **silhouette** = rembg/BiRefNet → IoU/Dice; **image-to-3D fidelity** = **Blender `--background` multi-view render → image metrics** (⚠️ headless GPU offscreen via pyrender/Open3D is **broken on Apple Silicon** → **reuse the Blender stage as the render bridge**); **subjective** = VLM-as-judge (Claude vision). All wrapped as **LangSmith custom evaluators**.
3. **Deterministic substrate = pytest + pydantic (schema gating) + syrupy (golden snapshots)** for harnesses 5–8 + the CI gate (this is also how LangSmith pytest evals run).
4. **DeepEval = OPTIONAL convenience only** — firewalled to metrics-only (**never enable its tracing**; it feeds Confident AI and would double-instrument LangGraph). Its DAG/Arena/multimodal catalog is largely subsumed by LangSmith-native + the component layer.
5. **Inspect AI = the one noted alternative** (vendor-neutral, native multimodal, agentic, OTel→LangSmith) if a heavier agentic-eval engine is ever wanted. **Avoid:** promptfoo/OpenAI Evals (OpenAI-owned → vendor-neutral conflict), Braintrust/Langfuse (redundant 2nd platform vs locked LangSmith), Ragas (RAG-shaped).
**Caveats:** Chamfer/Hausdorff/F-score need a **reference mesh** → use only on a held-out benchmark set; **live** generations score via appearance (render-compare to concept) + self-consistency (watertight/normals). Aesthetic/IQA models are **noisy/biased → directional signals, never hard gates**. Pin judge model + metric weights for CI determinism; cache weights for offline.
**Rationale:** Cohesive with the locked stack (one vendor for trace+eval+dataset+human-pref), zero redundant platform, vendor-neutral judge, and the mesh/image metric layer is portable if the runner ever changes.
**Fallback:** if LangSmith-native eval ergonomics disappoint, swap the *runner* to **DeepEval** or **Inspect AI** — the metric component layer is unchanged. **Related:** EVAL-001…009, R-010 + eval-deepdive (`tasks/we77jl8cj.output`). **Anchors:** §13.

## ADR-009 — App data store + secrets
**Status:** Locked (user) — **app-managed local Postgres.**
**Decision:** **App-managed local Postgres** as the relational/state store (projects, items, candidates, variants, swatches, overlays, runs/steps, validation, export, registries) + **pgvector** (future preference/similarity learning, OBS-004/EVAL-009) + **JSONB** for flexible spec/config blobs + **Alembic** migrations; LangGraph **PostgresSaver** shares the same DB (ADR-002). **Large artifacts (meshes/images/packages) stay as files on disk**, organized by project/item/candidate, referenced by path in Postgres. Postgres is **bundled + lifecycle-managed by the app** (start/health/stop) like the Python sidecar — not a user-installed dependency. **Secrets** (cloud/LLM API keys) in the **OS keychain** (encrypted-file fallback) — never in project files/logs. Accepted assets immutable without confirmation; backup = copy project folder + `pg_dump`.
**Rationale:** User-chosen; production-grade headroom (concurrent writers, rich relational queries over the lineage graph, pgvector) consistent with the real-infra posture; one DB for app + orchestration.
**Tradeoff/Risk:** bundling + signing/notarizing a Postgres binary on macOS adds packaging weight (RISKS); managing its lifecycle is core infra alongside the sidecar supervisor.
**Fallback:** **SQLite** (the lean local-first alternative) if bundling/managing Postgres proves too heavy — the data layer is abstracted behind a repository interface so the engine swap is contained. **Related:** REQ-D-101, REQ-S-101, R-005. **Anchors:** §10, §14.

## ADR-010 — Item-type model: open registries
**Status:** Locked (user, Phase-10 reframe).
**Decision:** No fixed enums. **Decorative generation open for any prop.** `PlacementType`, `FunctionalArchetype`, `DonorMapping` are **data-driven, validated registries**; adding a placement type = config, adding a functional archetype = registry entry + donor + test (no engine rewrite). Functional behavior seeded "as many as feasible." Out-of-scope frontier = arbitrary **novel scripted gameplay** (feasibility wall).
**Rationale:** User must not be boxed into a fixed item set; aligns with extensibility NFRs. **Related:** REQ-F-102/106. **Anchors:** §9.

## ADR-011 — Local image-to-3D fallback
**Status:** Locked.
**Decision:** Cloud-first (ADR-003). **Optional geometry-only local fallback** behind the same interface + a feature flag + quality/latency warning: **TRELLIS.2 MPS port**, pinned commit + smoke test; texturing pushed downstream. 48 GB is ample.
**Rationale:** Honors the user's "local if capable" intent without compromising production quality.
**Fallback:** SF3D/SPAR3D official MPS; else drop local entirely. **Related:** R-002. **Anchors:** §6, §7.

## ADR-012 — Build posture & scope sequencing
**Status:** Locked (Phase 0).
**Decision:** Production-grade engineering on a deliberately **narrow-but-open** product surface. **Spikes-first** sequencing: (1) GEOM/export spike, (2) image-to-3D bakeoff, (3) functional tuning-clone spike — de-risk feasibility (assumptions A1–A4) before breadth. Cuts are flagged deferrals. **Related:** Phase 8, RISKS. **Anchors:** §2, §15.

## ADR-013 — Platform / cross-platform
**Status:** Locked.
**Context:** Mac dev/test; "a few known users" (some Sims players are on Windows); the chosen stack (Electron, Python, Node @s4tk, Blender, cloud APIs) is largely cross-platform — bpy has Windows wheels too; only the **local-3D MPS fallback** is Apple-Silicon-only.
**Decision:** **Mac-first dev/test; architecture kept cross-platform-capable; Windows validation deferred** (not blocked). Avoid Mac-only assumptions outside the local-3D fallback + keychain specifics.
**Fallback:** n/a. **Invalidation:** a known user needs Windows now → promote Windows validation. **Related:** OQ11, R-008. **Anchors:** §2, §14.

## ADR-014 — LLM provider (planner/workers + eval judge)
**Status:** Locked (user) — **both providers, abstracted.**
**Context:** LLM powers Collection Planner, Style Bible, Concept-Prompt, Archetype-Mapper, Repair workers + the eval judge. Recurring cost; structured/agentic output quality matters.
**Decision:** **Provider-abstracted `LLMProvider` with two first-class providers: (a) Claude direct (Anthropic API) and (b) OpenRouter (model-agnostic routing).** Default worker + judge model = **Claude Sonnet/Opus-class** (strongest for this app's structured planning/mapping/judging), with OpenRouter for failover + easy per-task model A/B. Auth preference order: *Claude subscription/OAuth (if feasible) → Anthropic API key → OpenRouter.*
**⚠️ Feasibility flag (`research required`):** Claude **subscription/OAuth** auth is designed for Anthropic's first-party tools (claude.ai, Claude Code), **not** arbitrary third-party apps — using it programmatically in a custom desktop app is **likely not a supported path**. The realistic supported default is the **Anthropic API key** (or OpenRouter). Treat "use the subscription" as a verify-first item; do **not** architect around it as the primary auth.
**Rationale:** Abstraction keeps it swappable; Claude is strongest for structured work; OpenRouter adds resilience + model freedom. **Fallback:** swap model/provider via the abstraction. **Related:** ORCH-003, EVAL-*, REQ-S-101 (keys in keychain). **Anchors:** §5, §6, §13.

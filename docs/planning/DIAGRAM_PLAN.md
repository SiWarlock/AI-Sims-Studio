# DIAGRAM_PLAN — AI Sims Creator

> Phase-17 artifact, **anchors updated to the binding `ARCHITECTURE.md` `§`** (remap: `gap-audits/anchor-remap.md`).
> Favor diagrams that clarify hard mechanics (reconcile-resume, clone-a-donor, trust boundaries) + build seams.
> Format: **Mermaid** in Markdown unless noted.

## Full-Scope Architecture Diagram
**Purpose:** one map of the whole system + the 4 runtimes + trust boundaries.
**Must show:** Electron UI ↔ (IPC REST+SSE+cancel, token) ↔ Python sidecar (LangGraph + engine + reconciler +
repos) → subprocess workers (Blender CLI, Node @s4tk) + cloud adapters (image-gen, image-to-3D, LLM) ; stores
(Postgres + filesystem + keychain) ; LangSmith (fail-open) ; user's Sims 4 install (donors in / Mods out).
**Anchors:** §2, §2.5, §3, §4, §6, §7, §8, §9. **Format:** Mermaid flowchart. **Priority:** P0.

## Sub-Diagrams
### 1. Pipeline lifecycle sequence (prompt → installed CC)
Staged happy path + 5 gates (+ unsupported inline confirm). **Anchors:** §2, §5, §6, §17. Mermaid sequence. P0.

### 2. Item state machine (incl. audit-added states)
planned→…→export-ready + failed/excluded/**skipped/unsupported/cancelled** + test-installed→{in-game-verified|
failed}; scoped-repair re-entry. **Anchors:** §12, `DATA_MODEL.md`. Mermaid state. P0.

### 3. Run/Step (8-state) orchestration state machine  *(audit-added)*
pending→running→{succeeded|failed|waiting-for-user(interrupt gate)|cancelled}; failed→retrying; skipped.
**Anchors:** §6, §5, §12. Mermaid state. P0.

### 4. Reconcile-and-resume flow (crash recovery)
Reopen → enumerate incomplete threads → re-poll provider job_ids (decision-table: pollable / GC'd / succeeded-
but-missing) → reattach/retry → resume; @task idempotent submit; PID+heartbeat single-writer lock; Tripo 24h
re-download. **Anchors:** §6, §5, §17 (RISKS R8/R9). Mermaid flowchart. **P0 (highest-value mechanic).**

### 5. Export clone-a-donor flow (DBPF, atomic)
Donor index (§10) → read EA donor read-only → Blender game-ready GEOM + DST textures → @s4tk swap GEOM/
textures/COBJ/thumbnail, keep OBJD-tuning/FTPT/RIG/SLOT → temp-write→round-trip-validate→atomic-rename →
test-install copy. **Anchors:** §9, §8, §10, §15. Mermaid flowchart. **P0 (#1-risk subsystem).**

### 6. Subsystem dependency DAG & parallel tracks
Import-direction rule + frozen-first contracts + Tracks A–F with corrected cross-edges (C↔D GEOM seam, F→D
render-bridge, B→C/D). **Anchors:** §2.5. Mermaid flowchart. P1.

### 7. Trust-boundary / security diagram
The 6 boundaries (UI↔sidecar+token, sidecar↔cloud+output-validation, sidecar↔LangSmith+redaction, sidecar↔
workers+deterministic-gate, export↔game-install+atomic, keychain). **Anchors:** §16 (+ RISKS table). Mermaid
flowchart. P1.

### 8. Domain model / lineage
Entities + relationships + artifact lineage (Project→Plan→ItemSpec→Concept→Mesh→Variant→Swatch + Overlay;
registries). **Anchors:** §12, §13, `DATA_MODEL.md`. Mermaid ER/class. P1.

### 9. Supervisor / process lifecycle  *(audit-added)*
start/health/restart-with-backoff/stop + process-tree teardown for Postgres + sidecar + Blender + @s4tk; free-
port handshake. **Anchors:** §6, §19 (RISKS R10). Mermaid state/flowchart. P1.

### 10. Eval harness map
EVAL-001…009 → LangSmith datasets/experiments/pairwise/annotation + metric layer (trimesh/Open3D/torchmetrics/
**Blender render bridge**) + pytest/pydantic/syrupy CI; automatable vs manual tiers. **Anchors:** §15. Mermaid
flowchart. P2.

### 11. Deployment / packaging topology (macOS)
Electron + deep-signed/notarized sidecar + bundled Postgres(+pgvector) + Blender; data dir + Mods path; CI
sign/notarize/staple; rollback/snapshot. **Anchors:** §19 (RISKS R4). Mermaid flowchart. P2.

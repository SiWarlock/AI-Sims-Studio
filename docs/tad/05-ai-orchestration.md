# TAD — AI Orchestration Layer

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §7

> Model assignments, client wrappers, prompt library, cost tracking, determinism notes.

---

## 7. AI Orchestration Layer

### 7.1 Model Assignments (Current)

As established in the PRD and MVP Spec:

- **Collection planning:** Claude Sonnet 4.6 via Anthropic API (official SDK)
- **Per-item spec generation:** Claude Sonnet 4.6
- **Tuning value suggestion:** Claude Sonnet 4.6
- **Repair suggestions:** Claude Sonnet 4.6
- **Validation explanation rewriting:** Claude Haiku 4.5
- **Content policy prompt rephrasing (texture gen retry):** Claude Haiku 4.5
- **Texture generation:** model selected during Phase 1 POC (D-2), working default Flux 1.1 Pro via Replicate (official SDK)
- **Thumbnail rendering:** Blender (not AI)

### 7.2 Client Wrappers

Both Anthropic and Replicate SDKs are wrapped in thin internal clients that:

- Enforce request schemas (input validated before dispatch)
- Enforce response schemas (output validated before return)
- Log every call with prompt, model, latency, token counts, cost estimate
- Implement the retry policy from T-12
- Surface structured errors conforming to the error taxonomy

### 7.3 Prompt Library

Prompts live in a dedicated module (`sidecar/prompts/`) with one file per stage. Each prompt is a function that accepts a typed context object and returns the prompt string (or structured messages for Claude).

No prompts are hardcoded at call sites. All prompts are in the prompt library for discoverability, reviewability, and iteration.

### 7.4 Cost Tracking

Every AI call records its estimated cost in the `GenerationAttempt` record. Cost estimates use current published rates for Anthropic and Replicate. The admin mode includes a cost view summing costs per project, per day, and per session.

Cost is tracked for observability; there is no enforcement or rate limiting on cost in MVP.

### 7.5 Determinism Notes

AI outputs are not guaranteed deterministic even at temperature 0. Re-running a stage typically produces similar but not identical results. The pipeline treats AI outputs as generated artifacts that, once accepted, are persisted and not re-run unless the user explicitly requests regeneration.

Determinism is enforced at the non-AI stages: template loading, mesh assembly, thumbnail rendering (with fixed seeds in Blender), DBPF packaging, install.

---

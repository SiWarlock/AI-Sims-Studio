# MVP Spec — Decisions Deferred to Phase 1 (POC)

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §8

> Decisions D-1 through D-6 resolved during Phase 1 POC before Phase 2 begins.

---

## 8. Decisions Deferred to Phase 1 (POC)

The following decisions cannot be pre-committed without hands-on work against a live Sims 4 install or a live Replicate integration. Phase 1 must resolve them before Phase 2 begins.

- **D-1 — DBPF library choice.** Evaluate `sims4-tools` (community Python) vs rolling a custom thin wrapper on the documented DBPF format spec. Decision locked into TAD at end of Phase 1.
- **D-2 — Primary image generation model.** Evaluate Flux 1.1 Pro, Flux Dev, and any material-specific alternatives (MatForger-class, Materialize-class) available on Replicate. Quality of diffuse + coordinated normal/specular output is the selection criterion.
- **D-3 — Normal and specular map derivation strategy.** Either native multi-map generation from the image model, or post-process inference from diffuse via a height-map step. Decision depends on D-2 outcomes.
- **D-4 — Exact base-game reference object IDs.** For each of the four archetypes, identify the exact resource IDs in the user's Sims 4 install that will be cloned. Locked into TAD.
- **D-5 — Blender headless render recipe.** Settings for lighting, camera angle, and material pipeline that produce thumbnails matching in-game appearance. Locked as template authoring guidance.
- **D-6 — Texture resolution policy.** 2K diffuse is the baseline; confirm performance is acceptable and artifacts are not visible at in-game camera distance. Adjust if needed.

---

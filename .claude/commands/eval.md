---
description: Run a named eval class. Usage: /eval [category]
allowed-tools: Bash, Read
argument-hint: "[category|all]"
---

Run the named eval class.

Argument: `$ARGUMENTS` — one of the categories below; `all` runs the full suite. Default: prompt the user to pick if no argument.

<!-- ▼ EXAMPLE BLOCK [id=eval-body]: /eval body — illustrative shape. Replace wholesale with this project's eval classes. ▼ -->

The eval harnesses live in `evals/` (LangSmith-native backbone + a framework-agnostic metric component layer). All are dev/CI-only and never shipped. They run via `@pytest.mark.langsmith` over LangSmith datasets; aesthetic/IQA scores are **directional, never hard gates**. For offline/cheap CI, set `LANGSMITH_TEST_CACHE` + `LANGSMITH_TEST_TRACKING=false` and pin the judge model + metric weights (CI determinism). Run from the `evals/` area cwd (`uv` project).

Argument values — the 9 harnesses (EVAL-001…009, `ARCHITECTURE.md §15`):
- `001` — concept/plan-quality eval (LangSmith dataset + Claude-vision/judge over the planning + concept stages).
- `002` — image→3D mesh-fidelity eval: trimesh + Open3D (Chamfer/Hausdorff/F-score, ARM64) + PyMeshLab against the reference-mesh benchmark set; live generations score via Blender render-compare + self-consistency. (Render-only Blender is a hard prerequisite, §8.)
- `003` — image-quality eval: torchmetrics (LPIPS/SSIM/PSNR/CLIPScore) + IQA-PyTorch on concept/render outputs.
- `004` — Blender mesh-prep bakeoff: `{CLI vs bpy} × {deterministic vs +MCP-repair hybrid}` via `evaluate_comparative()` (CLI default; MCP arm restored per PRD; record verdict).
- `005` — silhouette / segmentation eval: rembg/BiRefNet IoU.
- `006` — registry-seed test set (reframed from golden archetype mappings): exercises the open PlacementType/FunctionalArchetype/DonorMapping registries.
- `007` — manual in-game tier (placeability/behavior test-install → ReviewEvent + annotation queue / human-preference).
- `008` — DBPF automatable tier: round-trip → reparse with `@s4tk` → assert required resource set + OBJD-tuning resolves + GEOM normals/UV/meshgroup.
- `009` — agent-trajectory eval: `agentevals` over the LangGraph repair/agent trajectories.
- `all` — full eval suite (EVAL-001…009)

## Mapping

| Argument | Command |
|---|---|
| `001` | `uv run pytest evals/harnesses/eval_001_plan.py -m langsmith -v` |
| `002` | `uv run pytest evals/harnesses/eval_002_mesh_fidelity.py -m langsmith -v` |
| `003` | `uv run pytest evals/harnesses/eval_003_image_quality.py -m langsmith -v` |
| `004` | `uv run pytest evals/harnesses/eval_004_blender_bakeoff.py -m langsmith -v` |
| `005` | `uv run pytest evals/harnesses/eval_005_silhouette.py -m langsmith -v` |
| `006` | `uv run pytest evals/harnesses/eval_006_registry_seed.py -m langsmith -v` |
| `007` | `uv run pytest evals/harnesses/eval_007_ingame_manual.py -m langsmith -v` |
| `008` | `uv run pytest evals/harnesses/eval_008_dbpf_roundtrip.py -m langsmith -v` |
| `009` | `uv run pytest evals/harnesses/eval_009_trajectory.py -m langsmith -v` |
| `all` | `uv run pytest evals/harnesses -m langsmith` |

(Adjust the file paths to the actual `evals/harnesses/*` names if they differ.)

## Pre-flight checks

1. **`LANGSMITH_API_KEY` set** (and `LANGSMITH_TRACING`/project as configured) — if not, abort with a message pointing at the eval setup doc; or run offline with `LANGSMITH_TEST_TRACKING=false` + `LANGSMITH_TEST_CACHE` for cached/cheap CI.
2. **Reference set + judge available** — the named CC0/hand-authored reference-mesh benchmark set is fetched (DVC location) for Chamfer/Hausdorff (002); the pinned judge model is reachable for the vision/subjective scorers. If a mesh/render eval (002/004), confirm render-only Blender is present (§8 prerequisite). If down, abort.
3. **Cost budget** — vision-judge + LangSmith runs cost money; if a cost cap is set, check current spend; abort if at cap.

## Output

Per category:
- Test count + pass rate (note: scores are directional, not hard gates)
- Metric breakdown (mesh: Chamfer/Hausdorff/F-score · image: LPIPS/SSIM/PSNR/CLIPScore · silhouette: IoU · subjective: judge verdict)
- Cost: total + per-item average (LangSmith + judge calls)
- New findings / regression status vs the pinned baseline

## Forbidden in this command

- **Running against any target other than the configured LangSmith project / allowlisted dataset.**
- **Auto-incrementing the cost cap.** If at cap, halt; surface to the user; the user decides.
- **Treating a directional score as a hard gate** — IQA/aesthetic scores never block; only the deterministic tiers (008 round-trip, 006 registry-seed) assert pass/fail.

<!-- ▲ END EXAMPLE BLOCK [id=eval-body] ▲ -->

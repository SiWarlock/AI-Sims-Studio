# MVP Spec — Phase 1 — Milestone Zero: Texturing Proof-of-Concept

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.2

> Prove the end-to-end pipeline with one template, one prompt, one in-game verification. Hard quality gate.

---

**Phase goal:** Prove the end-to-end pipeline from "user prompt" to "item appears correctly in Sims 4 Build/Buy catalog" using one template, one hardcoded prompt scenario, and the simplest possible implementation of each stage.

**Phase acceptance gate:** A maintainer can run the POC end-to-end and visually confirm a Y2K-themed lava lamp appears in the Build/Buy catalog of Sims 4, is placeable in the world, renders correctly, and matches the thumbnail shown at export time. The maintainer and primary user both confirm the visual quality meets the bar for full MVP commitment. If this gate fails, approach revision is required before Phase 2.

#### Tasks

**1.1 — Single template preparation**
Author or extract a single lava-lamp-shaped mesh following the Tier 1 template authoring standard, including clean UVs, three texture zones (base, vessel, cap), Sims tabletop footprint, and 2K-ready UV layout.

*Outputs:* One `.glb` file for `cylindrical_small_tabletop` with all required metadata.
*Dependencies:* None (can proceed in parallel with Phase 0 late tasks).
*Acceptance:* Template loads in Blender cleanly, renders correctly, and all three texture zones are addressable by UV bounds.

**1.2 — Replicate API integration**
Integrate with Replicate for image generation. Authenticate, submit requests, poll for completion, handle retries and errors.

*Outputs:* Python client module with a typed interface for submitting image generation jobs and retrieving results.
*Dependencies:* 0.2.
*Acceptance:* A test call produces an image for a simple prompt. Error conditions (auth failure, timeout, content policy rejection) are handled distinctly.

**1.3 — Image model evaluation (D-2, D-3)**
Evaluate candidate image models on Replicate for semi-Alpha material quality. Test: Flux 1.1 Pro, Flux Dev, any material-specific alternatives identified. Produce sample textures for the lava lamp's three zones using each candidate. Compare visual quality.

*Outputs:* Side-by-side comparison report with decisions D-2 and D-3 resolved.
*Dependencies:* 1.2.
*Acceptance:* A primary image model is selected. Normal and specular map strategy (native multi-map vs post-process derivation) is decided and documented.

**1.4 — Texture generation pipeline (POC scope)**
Build a minimal pipeline that, given a prompt and the lava lamp template's texture zones, generates diffuse, normal, and specular maps per zone using the selected model.

*Outputs:* Python function that accepts a prompt string and returns a complete texture set for the lava lamp template.
*Dependencies:* 1.1, 1.3.
*Acceptance:* Running with a Y2K prompt produces three coordinated texture maps per zone. Maps are visually consistent and at target resolution.

**1.5 — Blender headless render setup (D-5)**
Set up a headless Blender Python script that loads a template `.glb`, applies a texture set, and renders a thumbnail. Determine lighting, camera angle, and material settings that match in-game appearance.

*Outputs:* A Blender Python script invoked from the sidecar via subprocess that produces a PNG thumbnail. Decision D-5 locked.
*Dependencies:* 1.1, 1.4, 0.8.
*Acceptance:* Running the script produces a thumbnail PNG that visually matches in-game appearance.

**1.6 — DBPF library evaluation (D-1)**
Evaluate DBPF library options. Test reading and writing `.package` files with `sims4-tools` or equivalent. If no viable library exists, scope the custom implementation.

*Outputs:* Decision D-1 resolved. A working library (external or custom) capable of producing a valid `.package` file containing the resources required for a Build/Buy object.
*Dependencies:* None.
*Acceptance:* A test `.package` containing a known base-game-cloned object opens correctly in the game.

**1.7 — POC `.package` build pipeline**
Assemble a complete `.package` file for the lava lamp: the textured mesh, the thumbnail, the catalog metadata (hardcoded for POC), and a Build/Buy category assignment. Produce a valid DBPF.

*Outputs:* A `.package` file for one Y2K lava lamp.
*Dependencies:* 1.4, 1.5, 1.6.
*Acceptance:* The file validates structurally and contains all expected resources with correct TGI IDs.

**1.8 — Mods folder install for POC**
Copy the generated `.package` to the user's Sims 4 Mods folder.

*Outputs:* The file is installed into the detected Mods folder.
*Dependencies:* 1.7, 0.4.
*Acceptance:* File appears in the Mods folder with correct permissions.

**1.9 — In-game verification**
Maintainer launches Sims 4, verifies the lava lamp appears in the Build/Buy catalog in the expected category, places it in the world, and confirms it matches the thumbnail.

*Outputs:* Written verification notes with screenshots. If verification fails, documented failure modes and next steps.
*Dependencies:* 1.8.
*Acceptance:* Lava lamp appears in-game, is placeable, is visually correct. Both maintainer and primary user confirm visual quality meets MVP bar.

**1.10 — Phase 1 decision freeze**
Lock all decisions resolved during POC (D-1 through D-6) into the TAD. Document any deviations from the pre-Phase 1 assumptions.

*Outputs:* TAD is updated with final decisions. Any approach changes are recorded and approved.
*Dependencies:* 1.9.
*Acceptance:* TAD reflects the resolved decisions and the project is cleared to proceed to Phase 2.

---

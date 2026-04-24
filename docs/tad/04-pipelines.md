# TAD — Pipeline Architecture

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §6

> Every generation stage: collection planning, per-item spec, texture gen, thumbnail render, metadata, validation, DBPF packaging, auto-install, verification.

---

## 6. Pipeline Architecture

Every generation pipeline stage is implemented as a module with a standard shape:

- An input Pydantic schema
- An output Pydantic schema
- A pure async function `run(input) -> output` (or `run(input) -> AsyncIterator[ProgressEvent, output]`)
- Dependency-injected external clients (Anthropic, Replicate, Blender) so tests can mock them
- Structured logging with stage name, target entity, and outcome

### 6.1 Collection Planning Stage

**Input:** `PlanningInput` — user prompt, desired item count, style preference, template registry snapshot, optional reference inputs.

**Output:** `CollectionPlan` — theme summary, ordered item list, each with source request, selected template ID, confidence score, and optional warning text.

**Model:** Claude Sonnet 4.6 via Anthropic SDK, using tool use to enforce structured output.

**Prompt strategy:**

- System prompt describes the product's role, the template registry schema, the style preference, and the rules (no items outside the template registry's shape-matching capabilities, flag low-confidence matches, produce coherent plans).
- User prompt includes the creator's theme prompt and desired item count.
- Tool definition: a single `submit_plan` tool with the `CollectionPlan` schema.
- Temperature: low (~0.3) for consistency.

**Failure modes:**
- Rate limit: retry with exponential backoff
- Tool call malformed: retry up to 2 times with stricter prompt
- All retries exhausted: surface error to user with retry option

### 6.2 Per-Item Spec Generation Stage

**Input:** `SpecInput` — item source request, selected template (full schema), collection context (theme, palette, style preference, other items in collection for coherence).

**Output:** `ItemSpec` — per-zone prompts, name, description, tags, price, category, optional filter tag.

**Model:** Claude Sonnet 4.6 via Anthropic SDK.

**Prompt strategy:**

- System prompt describes the item spec generation task, the texture-zone schema, the style preference, and the rules (prompts must be image-model-ready, material-descriptive, photographic language for semi-Alpha; names must feel consistent with other items in collection).
- User prompt includes the source request, template schema, and collection context.
- Tool use: `submit_item_spec` tool with the `ItemSpec` schema.

**Parallelization:** Items in a collection can be spec-generated in parallel. The collection context is passed to each call so coherence is maintained across parallel generations.

**Failure modes:**
- Same as planning stage with per-item isolation (one item's failure does not block others)

### 6.3 Texture Generation Stage

**Input:** `TextureGenInput` — item spec, template schema (for zone UV bounds), swatch index (for seed variation), style preference.

**Output:** `TextureSet` — per-zone diffuse/normal/specular PNG paths on disk.

**Model:** decision D-2 (selected during Phase 1 POC). Default working assumption: Flux 1.1 Pro via Replicate for diffuse; normal and specular handled per D-3.

**Pipeline:**

1. For each texture zone in the template, construct the image generation prompt from `ItemSpec.texture_zone_prompts[zone]` combined with material hints and style directives.
2. Submit the diffuse generation request to Replicate.
3. Per D-3: either submit coordinated normal/specular requests, or derive normal/specular from diffuse via a height-map inference step.
4. Download results, save to the swatch's texture folder.
5. Validate output images (correct dimensions, not corrupted, plausibly matching the prompt via a simple sanity check such as non-uniform content).
6. Return the `TextureSet` record.

**Parallelization:** Swatches across items, and zones within a swatch, can generate in parallel. Concurrency is capped to respect Replicate rate limits (working default: 4 concurrent requests).

**Failure modes:**
- Replicate timeout: retry once with same seed
- Content policy rejection: retry once with prompt rephrased by Haiku
- Zone-level failure: mark zone failed, continue other zones
- Swatch-level failure (all zones failed): mark swatch failed, item still usable with remaining swatches

### 6.4 Thumbnail Render Stage

**Input:** `ThumbnailInput` — item, primary swatch's texture set, template mesh path.

**Output:** `ThumbnailArtifact` — paths to rendered PNGs (item catalog thumbnail, per-swatch catalog thumbnails, large preview for app).

**Tool:** Blender invoked as subprocess.

**Pipeline:**

1. Sidecar prepares a Blender job spec (template mesh, texture maps per zone, camera and lighting settings from D-5).
2. Sidecar writes the job spec to a temp file and invokes Blender headless:
   `blender --background --python scripts/render_thumbnail.py -- <job_spec_path>`
3. Blender script loads the `.glb`, assigns materials from the texture maps, renders at configured resolutions (catalog thumbnail 128×128, swatch thumbnail 64×64, app preview 512×512 per T-9 working assumption).
4. Blender writes PNG outputs to predetermined paths.
5. Sidecar reads outputs, validates them, and returns paths.

**Parallelization:** Thumbnail rendering is sequential per item (one Blender subprocess at a time) to avoid Blender lock issues. Items can render in parallel only if separate Blender instances are managed carefully; for MVP, thumbnail rendering is strictly serial.

**Failure modes:**
- Blender subprocess failure: retry once (likely transient)
- Repeated failure: mark item needs-review with admin-visible detail

### 6.5 Metadata Finalization Stage

Not a separate AI call. Takes `ItemSpec` auto-suggestions and merges with any user edits stored on the `Item`. User edits always win. Final metadata is persisted to the item record.

### 6.6 Validation Stage

**Input:** A collection ID.

**Output:** `ValidationResult` with errors and warnings.

**Checks (MVP scope):**

1. **Asset completeness per item** — required fields present, thumbnails exist, textures exist.
2. **Metadata completeness** — name not empty, price in valid range, category is a recognized Build/Buy category.
3. **DBPF integrity** — for built packages, verify DBPF header, TGI resource IDs non-colliding, required resources present.
4. **Tuning integrity** — for functional items, verify cloned tuning is valid XML with all expected fields present and references resolvable.
5. **Archetype-template compatibility** — confirm any functional overlays' archetypes are in their item's template's compatibility list.
6. **Project consistency** — no dangling references, no orphaned items.

Each check is an independent module returning zero or more `ValidationIssue`s. Validation is deterministic and re-runnable.

### 6.7 DBPF Packaging Stage

**Input:** A collection ID, plus per-item variant choices (decor-only, functional, or both).

**Output:** `ExportArtifact` — a `.package` file on disk.

**Pipeline (one `.package` per collection, per T-8):**

1. Initialize a new DBPF container.
2. For each included item:
   - Encode texture maps to DDS (DXT1 for diffuse without alpha, DXT5 with alpha, per standard Sims conventions)
   - Assemble the textured mesh as a `.geom` or Sims-appropriate mesh resource
   - Generate TGI resource IDs for all resources (mesh, textures, catalog entry, string table entries, thumbnail)
   - Build the catalog entry (object definition) with metadata from `ItemMetadata`
   - Build the string table entries for name and description
   - Build the thumbnail resource
3. If the item has a functional overlay:
   - Retrieve the cloned-and-edited tuning from the functional overlay record
   - Add tuning resources to the package with new TGI IDs
   - Update catalog entry to reference the functional tuning
4. Write the DBPF container to disk.
5. Compute SHA-256 of the output file.
6. Return `ExportArtifact`.

**Determinism:** The same input produces byte-identical output. TGI ID generation uses a deterministic hash from the item ID + resource kind so rebuilds are stable.

### 6.8 Auto-Install Stage

**Input:** An `ExportArtifact`.

**Output:** Updated `ExportArtifact` with `install_path` populated.

**Pipeline:**

1. Confirm Mods folder path is available (re-detect if stale).
2. Check for existing file at target path:
   - If missing: copy file directly
   - If exists and SHA-256 matches: skip, report "already installed"
   - If exists and SHA-256 differs: prompt user (overwrite / rename / skip)
3. Copy with fsync to ensure file is flushed.
4. Update the artifact record with `install_path` and `installed_at`.

**Failure modes:**
- Permission denied: prompt user for alternative location or manual install
- Disk full: clear error with remediation

### 6.9 Verification Stage

Not a generation pipeline. A UI flow that:

1. Displays a "Launch Sims" button
2. Presents a per-item checklist for the user to mark "appeared correctly" or "something looks wrong"
3. Persists verification state to the `ExportArtifact.verified_in_game` field and per-item notes

---

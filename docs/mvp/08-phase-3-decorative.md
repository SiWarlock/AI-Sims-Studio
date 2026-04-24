# MVP Spec — Phase 3 — Decorative Generation Pipeline

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.4

> Collection planning, per-item spec generation, texture pipeline at scale, thumbnail rendering, metadata, collection board and item detail UI.

---

**Phase goal:** Build the full decorative generation flow: collection planning, per-item spec generation, texture generation at scale, thumbnail rendering, metadata generation, and the creator-facing UI to review and iterate.

**Phase acceptance gate:** A user can enter a prompt, receive a plan, edit the plan, generate a complete multi-item collection, review items on a collection board, open item detail views, regenerate items and swatches, and edit metadata. No export or functional capability yet.

#### Tasks

**3.1 — Anthropic API integration**
Integrate with the Anthropic API for Claude Sonnet 4.6 and Haiku 4.5. Authenticate, submit structured output requests, handle retries and errors. Support tool use for structured response enforcement.

*Outputs:* Python client with typed interfaces for the planning and metadata stages.
*Dependencies:* 0.2.
*Acceptance:* Test calls produce structured responses. Errors are handled distinctly.

**3.2 — Collection planning stage**
Implement the planning stage. Takes user prompt + desired count + template registry. Produces a structured plan: theme summary, item list, template match per item with confidence score, style attributes, palette direction.

*Outputs:* Python function returning a typed `CollectionPlan` object.
*Dependencies:* 3.1, 2.4.
*Acceptance:* For a Y2K bedroom prompt with 6 items, produces a coherent plan with sensible template matches. Low-confidence matches are flagged. User can request fewer or more items.

**3.3 — Per-item spec generation stage**
Implement the per-item spec stage. Takes a plan item + its template schema + collection-level style context. Produces a typed `ItemSpec`: per-zone texture prompts, item name, description, tags, price suggestion, Build/Buy category, optional custom catalog filter tag.

*Outputs:* Python function returning a typed `ItemSpec` object.
*Dependencies:* 3.1, 2.4.
*Acceptance:* For a planned Y2K lava lamp, produces per-zone prompts that feel appropriately coordinated, plus sensible metadata.

**3.4 — Per-item texture generation pipeline**
Build the pipeline that takes an item spec plus its template's texture-zone schema and produces coordinated diffuse, normal, and specular texture maps per zone, per swatch, via Replicate.

*Outputs:* Async Python function `generate_textures(item_spec, template, swatch_count) -> TextureSet` returning a fully populated TextureSet. Includes retry logic and per-zone prompt construction.
*Dependencies:* 1.4, 3.3.
*Acceptance:* Generates a 3-swatch texture set for any template given an item spec. Maps per swatch are visually coordinated.

**3.5 — Thumbnail rendering pipeline**
Generalize the Phase 1 thumbnail pipeline to work for all templates with all texture sets. Render deterministic thumbnails per item per swatch.

*Outputs:* Python function that accepts a template + texture set and returns a thumbnail PNG.
*Dependencies:* 1.5, 2.4, 3.4.
*Acceptance:* Produces thumbnails for every template type. Thumbnails match the in-game appearance they will have once exported.

**3.6 — Collection orchestration**
Build the orchestrator that takes an approved plan and executes full generation: per-item spec generation, per-item texture generation with N swatches, thumbnail rendering, metadata finalization. Handles failures per item without aborting the whole collection.

*Outputs:* Async orchestrator with progress events surfaced to the UI.
*Dependencies:* 3.2, 3.3, 3.4, 3.5.
*Acceptance:* Given an approved plan, generates all items. Per-item failures are isolated and reported.

**3.7 — Collection plan review UI**
Build the UI surface where the user reviews the proposed plan, edits the item list (add, remove, reorder, rename intent), sees template match confidence per item, resolves low-confidence items (proceed / skip / rephrase), and triggers generation.

*Outputs:* React screens with full interaction.
*Dependencies:* 3.2, 0.6.
*Acceptance:* User can reach this screen from the new-project flow, make edits, and trigger generation.

**3.8 — Collection board UI**
Build the collection board: grid of items with thumbnails, status indicators, include/exclude toggles, functional-candidate indicators, project-level actions. Updates live as generation progresses.

*Outputs:* React screen with live update via IPC events.
*Dependencies:* 3.6, 0.6.
*Acceptance:* User can see items populate as they generate. Include/exclude toggles work. Clicking an item opens its detail view.

**3.9 — Item detail UI**
Build the item detail view: large preview, swatch list with per-swatch regenerate, metadata view and edit form, regenerate item, replace item, make-functional button (disabled until Phase 5).

*Outputs:* React screen with full editing and regeneration controls.
*Dependencies:* 3.8, 3.6.
*Acceptance:* User can regenerate individual swatches, regenerate the full item, replace the item, and edit metadata fields.

**3.10 — Metadata editing and validation**
Implement metadata editing: name, description, tags, price, Build/Buy category, custom catalog filter tag. Validate edits (name not empty, price in valid range, etc.).

*Outputs:* Editing functionality with client-side and server-side validation.
*Dependencies:* 3.9.
*Acceptance:* Edits persist to project storage. Invalid inputs are rejected clearly.

**3.11 — Progress and status event system**
Implement the event system that surfaces generation progress to the UI in real time. Status transitions per item (planned → generating → generated → needs_review etc.) are reflected immediately.

*Outputs:* Event bus with typed events, subscriptions from UI components.
*Dependencies:* 3.6, 0.2.
*Acceptance:* During generation, the UI shows live progress per item. Errors surface immediately with user-friendly messages.

**3.12 — Style parameter architecture**
Ensure the `style_preference` parameter is threaded through the entire pipeline end-to-end, even though only `semi_alpha` is implemented. Schemas accept it, prompts reference it, future MM can be added by extending handlers without schema changes.

*Outputs:* Every relevant function signature and schema includes `style_preference`. Semi-Alpha is the only implementation path; MM raises a clear "not yet implemented" exception if invoked.
*Dependencies:* 3.3, 3.4.
*Acceptance:* Schema inspection confirms the parameter exists. A maintainer could add MM handlers in v1.5 without altering schemas.

---

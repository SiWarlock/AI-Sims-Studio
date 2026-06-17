# DATA_MODEL — AI Sims Creator

> arch-draft (Brain 1) rough draft. Phase-5 artifact. Domain language + entities + state machines +
> invariants. **Not** physical schema — that's the TAD/ARCHITECTURE's job. Source = PRD §20 + Phase 0–4
> interview decisions. **Source of truth (binding, per ARCHITECTURE.md §12/§13 — supersedes earlier drafts):
> app-managed local Postgres is authoritative** for ALL relational/state (incl. authoritative Trace summaries +
> ReviewEvents); **filesystem = artifact bytes only**, referenced by path (write-bytes-then-commit-row);
> **LangSmith = derived, fail-open mirror**; **registries = version-controlled config files** loaded into
> Postgres as a cache. (Earlier "local project folder = source of truth" phrasing is corrected here.)

---

## Core Entities
| Entity | Definition | Key Fields | Source of Truth |
|---|---|---|---|
| **Project** | A user content project | id, name, prompt, styleNotes, desiredItemCount, outputMode, generationMode, status, created/updated, planRef, exportSettings, runRefs | local store |
| **CollectionPlan** | Structured plan from prompt (versioned) | id, projectId, styleBibleRef, itemSpecs[], version, approvalStatus | local store |
| **StyleBible** | Collection-level style lock | themeSummary, palette, materials, shapeLanguage, eraRefs, renderStyle, negativeConstraints | CollectionPlan |
| **ItemSpec** | A planned object (the stable item identity) | id, displayName, description, required?, **archetype**, placementCategory, functionalEligibility, conceptPrompt, meshContext, swatchPlan, status(13), include? | CollectionPlan |
| **ConceptCandidate** | A generated concept image | id, itemId, prompt, imagePath, provider, status, userDecision, readinessScore? | ItemSpec |
| **MeshCandidate** | A generated 3D asset candidate | id, itemId, sourceConceptId, adapter, adapterConfig, meshPath, texturePaths[], qaStatus+score, cleanupStatus, normalizedIntermediatePath, previewPath, userDecision | ItemSpec |
| **AssetVariant** | An accepted/selectable realized item | id, itemId, conceptRef, meshRef, **swatches[]**, previewRefs, exportReadiness | ItemSpec |
| **Swatch** | A color/texture preset of one mesh (Sims-native) | id, variantId, label, texturePaths, thumbnailPath, isDefault | AssetVariant |
| **FunctionalOverlay** | Behavior layered on the SAME item identity | id, sourceItemId, sourceVariantId, **archetype** (audio/light/mirror/moodlet), donorRef, userConfig, behaviorSummary, validationStatus, exportMode (decor/functional/both) | ItemSpec |
| **PlacementType** | *Registry entry* — how/where an object places (open, extensible) | id, name (surface/floor/wall/shelf/ceiling/…), donorRef, footprintRules | registry (data-driven) |
| **FunctionalArchetype** | *Registry entry* — a cloneable in-game behavior (open, extensible) | id, name, donorRef, tuningGraftRules, eligibilityRules, validationRules | registry (data-driven) |
| **DonorMapping** | *Registry entry* — EA donor + clone-and-replace rules, keyed by placement-type / archetype | key(placementType\|archetype), donorObjectKey, requiredResources[], tuningKeys[], preserveKeys[] | registry (data-driven) |
| **PipelineRun** | A graph/workflow run | id, projectId, itemId?, runType, status, steps[], traceRef, start/end | local store |
| **Step** | One stage within a run | id, runId, name, state(8), inputs, outputs/artifactRefs, attempts, error?, cost?, latency? | PipelineRun |
| **ValidationResult** | One validation finding | id, scope(project/item/mesh/overlay/export), severity(error/warn/info/pass), message, suggestedAction, relatedRef | derived per run |
| **ExportArtifact** | Final installable output | id, projectId, outputPath, includedItems[], functionalOverlays[], buildStatus, reportPath, timestamp | local store |
| **ExportReport** | Human-readable export summary | projectName, timestamp, included/excluded, functional, validationSummary, warnings, artifactPaths, runRef | ExportArtifact |
| **Trace** | Per-run observability record | projectId, itemId?, prompt, planVersion, specVersion, worker, model/tool, inputs, outputs/artifactRefs, start/end, status, error, cost/latency, validation, review events | append-only |
| **ReviewEvent** | User approve/reject/note (preference data) | projectId, itemId, candidateId, artifactType, decision, reason?, notes, timestamp | append-only |
| **ProviderConfig / Secret** | Adapter + credential config | provider, mode(mock/real), endpoint, modelId, params; secrets in OS keychain | local config |

## Relationships
Project 1–1 CollectionPlan (versioned) · CollectionPlan 1–1 StyleBible · CollectionPlan 1–N ItemSpec ·
ItemSpec 1–N ConceptCandidate · ConceptCandidate 1–N MeshCandidate · ItemSpec 1–N AssetVariant ·
AssetVariant 1–N **Swatch** · ItemSpec 0–1 FunctionalOverlay (extension, same identity) · Project 1–N
PipelineRun · PipelineRun 1–N Step · (any scope) 1–N ValidationResult · Project 1–N ExportArtifact 1–1
ExportReport · everything 1–N Trace/ReviewEvent.

## State Machines
**Project:** `created → planned → generating → curating → validating → exporting → {exported | export-failed}`
(curating⇄generating on regenerate; validating→curating on blockers; exporting→curating on export cancel/fail;
any→generating on new run). *(audit-added: `exporting`/`export-failed`.)*

**Item (13 base states + audit-added):** `planned → concept-pending → concept-generating → concept-review-needed
→ mesh-pending → mesh-generating → mesh-QA-pending → blender-cleanup-pending → preview-ready → needs-review →
export-ready`; plus `failed` (from any generating/QA/cleanup; → retry returns to that state's pending),
`excluded` (from any state; reversible to needs-review), and **audit-added:** `skipped` (≠ excluded; abandoned at
concept-review without a mesh; re-activate → concept-pending), `unsupported` (no resolvable donor/placement;
inline-confirm → convert to `planned`, or terminal), user-`cancelled` (→ prior stage's `*-pending`),
`test-installed → {in-game-verified | in-game-failed}` (verification loop, records a ReviewEvent). Forbidden:
mesh before concept-approval; export-ready without a selected variant + passing item validation.

**Run/Step (8 states):** `pending → running → {succeeded | failed | waiting-for-user | cancelled}`;
`failed → retrying → running`; `waiting-for-user → running` (on gate decision); `skipped` terminal.

**AssetVariant (audit-added):** `candidate → selected → locked`; `selected → superseded` on re-selection;
exit from `locked` is confirmation-gated (Invariant 4). This is the state the export precondition ("selected
AssetVariant") and immutability invariant bind to.

**ConceptCandidate:** `generated → {approved | rejected | superseded}`.
**MeshCandidate:** `generated → qa(pass|fail) → cleanup(pending→running→done|failed) → {accepted | rejected | superseded}`.
**FunctionalOverlay:** `draft → validated → {approved | invalid}`; **audit-added:** `invalid → draft`
(reconfigure-and-revalidate on compatibility failure).
**ExportArtifact:** `building → {success | success-with-warnings | partial | failed | cancelled}`.

## Invariants (must never break)
1. An item is **exportable** only if: included = true ∧ has a selected AssetVariant ∧ item validation has no
   blockers (FR-VAL-004).
2. A FunctionalOverlay references the **same ItemSpec identity** as its decor asset — never a duplicate item
   (PRD principle 5 "one asset, multiple outputs").
3. Every generated artifact records **lineage** to its inputs (mesh←concept←spec←plan←prompt; overlay←variant
   +config) (OBS-003).
4. **Accepted/selected assets are immutable** without explicit user confirmation (NFR §22.6).
5. **Approval gates are ordered**: no mesh before concept approved; no overlay before variant selected; no
   export before export approval (PIPE-005).
6. Only **registered** placement-types/archetypes are assignable (open registries, validated — not fixed
   enums); only **eligible** items (per the archetype's eligibility rules) can receive overlays (FR-FUNC-002).
   Decorative generation itself is unconstrained by item type.
7. Every exportable AssetVariant has **≥1 Swatch** (the default appearance); multi-swatch supported.
8. A single item/step **failure never corrupts** the project or other items (PIPE-004 / FR-3D-006).
9. Every state-changing pipeline action emits a **Trace** and updates **Step state** (OBS-001 / ORCH-002).
10. Cloud generation actions and MCP/agent actions must pass **deterministic validation** before being
    written to project state (ORCH-004 / MCP-003).

## Swatch vs Variant (resolved)
`locked decision` **Sims-native, multi-swatch in MVP.** *Swatch* = a color/texture preset of ONE mesh
(multiple presets export into one object package, Sims-native); *Variant* = an alternate generated mesh
candidate the user can select as the item's appearance. MVP **generates + exports multiple recolors
(swatches) per object**; this elevates a Swatch/Texture worker, multi-preset DBPF export, and swatch UI to
in-scope (recorded in scope inference + risks).

## Data Authority / Freshness  *(reconciled to ARCHITECTURE.md §12/§13)*
- **Authoritative = app-managed Postgres:** Project, CollectionPlan, StyleBible, ItemSpec, candidates, variants,
  swatches, overlays, runs/steps, validation results, export artifacts (rows), config, **Trace summaries +
  ReviewEvents** (authoritative locally for OBS-004/EVAL-009).
- **Filesystem = artifact BYTES only** (meshes/images/packages/previews), referenced by path; write-bytes-then-
  commit-row so a crash leaves an orphan file, never a dangling ref. Sidecar repo layer is the only writer.
- **Registries = version-controlled config files** (source of truth) loaded/validated into Postgres as a cache.
- **LangSmith = derived, fail-open mirror** of traces (dev/observability UX only) — not a source of truth.
- **Derived/display (recomputable):** status badges, cost/latency estimates, validation rollups, thumbnails,
  preview composites. May be stale briefly; never the source of truth.

## Glossary
Build/Buy · archetype (supported object category) · donor object (EA object cloned) · DBPF (.package format)
· OBJD (object definition) · MODL/MLOD/GEOM (model + LOD + mesh resources) · LOD (level of detail) · FTPT
(footprint) · rig (object bone/slot skeleton) · tuning (XML behavior resources) · swatch/preset · style
bible · functional overlay · vertical slice (the CD-player anchor path).

## Ambiguous Terms (→ research/spike)
- Exact required DBPF resource set per archetype and per-archetype EA **donor** choices — `research required`.
- "Game-ready geometry" precise bar (poly budget, LOD count, rig/slot requirements per Build/Buy category) —
  `research required` + Blender spike.
- "Moodlet/vibe" behavior in-game (environment score vs buff overlay) — `open question` + functional spike.

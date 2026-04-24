"""
Sharding script for AI Sims Creator documentation.

Splits the five monolithic docs (PRD, MVP, TAD, API, Diagrams) into
section-scoped shards under docs/{prd,mvp,tad,api,diagrams}/.

Usage:
    python shard_docs.py

The script reads from docs/MONOLITHIC/ and writes to docs/{area}/.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parent
MONO = ROOT / "docs" / "MONOLITHIC"


@dataclass
class Shard:
    """A shard is a set of top-level sections from a monolithic doc."""

    filename: str
    title: str
    sections: list[int]  # section numbers to include (e.g. [3, 4, 9])
    description: str  # one-line description for the index


@dataclass
class SourceDoc:
    """A monolithic doc being sharded."""

    monolithic_filename: str
    output_subdir: str
    area_label: str
    shards: list[Shard]


# Regex that matches a top-level section header: "## N. Title"
SECTION_RE = re.compile(r"^## (\d+)\.\s+(.+?)$", re.MULTILINE)


def parse_sections(content: str) -> dict[int, tuple[str, str]]:
    """
    Parse a monolithic doc into a map of section_number -> (title, body).

    Body includes everything from the section header to (but not including)
    the next top-level section header.
    """
    matches = list(SECTION_RE.finditer(content))
    sections: dict[int, tuple[str, str]] = {}

    for i, match in enumerate(matches):
        section_num = int(match.group(1))
        title = match.group(2).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].rstrip() + "\n"
        sections[section_num] = (title, body)

    return sections


def build_shard_content(
    shard: Shard,
    sections: dict[int, tuple[str, str]],
    area_label: str,
    monolithic_filename: str,
) -> str:
    """Assemble a shard file's full content."""
    lines: list[str] = []
    lines.append(f"# {shard.title}\n")
    lines.append(
        f"> **Source:** `docs/MONOLITHIC/{monolithic_filename}` · "
        f"**Area:** {area_label} · "
        f"**Sections:** {', '.join(f'§{n}' for n in shard.sections)}\n"
    )
    lines.append(f"> {shard.description}\n")
    lines.append("---\n")

    for section_num in shard.sections:
        if section_num not in sections:
            raise ValueError(
                f"Section {section_num} not found for shard {shard.filename}"
            )
        _, body = sections[section_num]
        lines.append(body)
        lines.append("\n")

    return "\n".join(lines).rstrip() + "\n"


def shard_doc(doc: SourceDoc, root: Path) -> list[Path]:
    """Shard one monolithic doc. Returns list of produced paths."""
    mono_path = root / "docs" / "MONOLITHIC" / doc.monolithic_filename
    content = mono_path.read_text(encoding="utf-8")
    sections = parse_sections(content)

    out_dir = root / "docs" / doc.output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    produced: list[Path] = []
    for shard in doc.shards:
        body = build_shard_content(
            shard, sections, doc.area_label, doc.monolithic_filename
        )
        out_path = out_dir / shard.filename
        out_path.write_text(body, encoding="utf-8")
        produced.append(out_path)

    return produced


# --------------------------------------------------------------------------- #
# PRD shards
# --------------------------------------------------------------------------- #
PRD = SourceDoc(
    monolithic_filename="PRD.md",
    output_subdir="prd",
    area_label="PRD",
    shards=[
        Shard(
            filename="00-document-meta.md",
            title="PRD — Document Meta, Deferred Questions, Next Documents",
            sections=[1, 2, 37, 38],
            description="Document status, purpose, deferred open questions, and recommended next documents.",
        ),
        Shard(
            filename="01-product-summary.md",
            title="PRD — Product Summary, Positioning, and Thesis",
            sections=[3, 4, 9],
            description="What the product is, its category and promise, and the core thesis for how it's built.",
        ),
        Shard(
            filename="02-users.md",
            title="PRD — Users and Problem Statement",
            sections=[5, 6],
            description="Primary creator, administrator, and future users. The problems this product solves.",
        ),
        Shard(
            filename="03-goals-principles.md",
            title="PRD — Goals, Non-Goals, and Product Principles",
            sections=[7, 8, 11],
            description="Primary and secondary goals, explicit non-goals, and product principles.",
        ),
        Shard(
            filename="04-mvp-definition.md",
            title="PRD — MVP Definition and Scope",
            sections=[10, 12, 13],
            description="MVP objective, anchor scenario, playable-in-game promise, core capabilities, in- and out-of-scope.",
        ),
        Shard(
            filename="05-content-and-style.md",
            title="PRD — Content Categories, Visual Style, and Template Library",
            sections=[14, 15, 16],
            description="Supported content categories and archetypes, visual style strategy (semi-Alpha first), two-tier template library model.",
        ),
        Shard(
            filename="06-user-stories.md",
            title="PRD — User Stories",
            sections=[17],
            description="Creator, administrator, and UX stories.",
        ),
        Shard(
            filename="07-functional-requirements.md",
            title="PRD — Functional Requirements",
            sections=[18],
            description="All functional requirements FR-001 through FR-087 across project management, planning, templates, generation, functional overlay, review, validation, export, and admin mode.",
        ),
        Shard(
            filename="08-non-functional-and-workflows.md",
            title="PRD — Non-Functional Requirements, Screens, and Workflows",
            sections=[19, 20, 21],
            description="Non-functional requirements (reliability, usability, etc.), screen inventory, and primary workflows A through D.",
        ),
        Shard(
            filename="09-acceptance-and-guardrails.md",
            title="PRD — Acceptance, Constraints, Guardrails, and Summary",
            sections=[22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 39],
            description="Acceptance criteria AC-001 through AC-016, feature-area requirements, playable-in-game definition, trust/data/AI/error/logging/security/quality requirements, edge cases, metrics, release criteria, implementation guardrails, assumptions, and executive summary.",
        ),
    ],
)


# --------------------------------------------------------------------------- #
# MVP shards
# --------------------------------------------------------------------------- #
MVP = SourceDoc(
    monolithic_filename="MVP_Specification.md",
    output_subdir="mvp",
    area_label="MVP Spec",
    shards=[
        Shard(
            filename="00-overview.md",
            title="MVP Spec — Overview and MVP Definition",
            sections=[1, 2, 3, 5],
            description="Document status, purpose, what MVP v1.0 is and is not, and explicit deferrals.",
        ),
        Shard(
            filename="01-phase-overview.md",
            title="MVP Spec — Phase Overview and Gating",
            sections=[4],
            description="The eight MVP phases and their gating structure. Phase 1 is a hard quality gate.",
        ),
        Shard(
            filename="02-template-roster.md",
            title="MVP Spec — Template Roster",
            sections=[6],
            description="The 19 Tier 1 template primitives that ship with MVP, with schema and authoring standards.",
        ),
        Shard(
            filename="03-archetype-mapping.md",
            title="MVP Spec — Functional Archetype → Reference Object Mapping",
            sections=[7],
            description="Light on/off, audio device, mirror, moodlet emitter — reference targets, selection criteria, compatible templates, and configuration parameters.",
        ),
        Shard(
            filename="04-deferred-decisions.md",
            title="MVP Spec — Decisions Deferred to Phase 1 (POC)",
            sections=[8],
            description="Decisions D-1 through D-6 resolved during Phase 1 POC before Phase 2 begins.",
        ),
        Shard(
            filename="05-phase-0-foundation.md",
            title="MVP Spec — Phase 0: Foundation",
            sections=[],  # Phase tasks live under §9 subsections; handled specially below
            description="App shell, project storage, platform detection, and basic UI scaffolding. No AI, no templates.",
        ),
        Shard(
            filename="06-phase-1-poc.md",
            title="MVP Spec — Phase 1: Milestone Zero (Texturing POC)",
            sections=[],
            description="Prove the end-to-end pipeline with one template, one prompt, one in-game verification. Hard quality gate.",
        ),
        Shard(
            filename="07-phase-2-templates.md",
            title="MVP Spec — Phase 2: Template Library",
            sections=[],
            description="Author all 19 Tier 1 templates and build the template loader infrastructure.",
        ),
        Shard(
            filename="08-phase-3-decorative.md",
            title="MVP Spec — Phase 3: Decorative Generation Pipeline",
            sections=[],
            description="Collection planning, per-item spec generation, texture pipeline at scale, thumbnail rendering, metadata, collection board and item detail UI.",
        ),
        Shard(
            filename="09-phase-4-validation-export.md",
            title="MVP Spec — Phase 4: Validation, Export, and Auto-Install",
            sections=[],
            description="Structural validation, export screen, DBPF build pipeline, Mods folder auto-install.",
        ),
        Shard(
            filename="10-phase-5-functional.md",
            title="MVP Spec — Phase 5: Functional Overlay",
            sections=[],
            description="Archetype configuration, tuning extraction, clone pipeline, functional variant packaging.",
        ),
        Shard(
            filename="11-phase-6-admin.md",
            title="MVP Spec — Phase 6: Admin Mode",
            sections=[],
            description="Template browser, base-game importer, Tier 2 promotion editor, logs viewer, job history, reference object browser.",
        ),
        Shard(
            filename="12-phase-7-polish.md",
            title="MVP Spec — Phase 7: Cross-Platform Hardening and Polish",
            sections=[],
            description="Windows parity, path edge cases, Blender discovery polish, documentation deliverables.",
        ),
        Shard(
            filename="13-acceptance-criteria.md",
            title="MVP Spec — MVP Acceptance Criteria",
            sections=[10],
            description="MVP-AC-001 through MVP-AC-030 — the complete testable criteria for MVP release.",
        ),
        Shard(
            filename="14-testing-strategy.md",
            title="MVP Spec — Testing Strategy",
            sections=[11],
            description="Unit, integration, manual acceptance tests, and POC visual quality gate.",
        ),
        Shard(
            filename="15-supporting.md",
            title="MVP Spec — Decisions Log, Docs, Risks, Success, and Summary",
            sections=[12, 13, 14, 15, 16, 17],
            description="Decisions resolution log, documentation deliverables, risks and mitigations, release success criteria, post-MVP directions, and executive summary.",
        ),
    ],
)


# --------------------------------------------------------------------------- #
# TAD shards
# --------------------------------------------------------------------------- #
TAD = SourceDoc(
    monolithic_filename="TAD.md",
    output_subdir="tad",
    area_label="TAD",
    shards=[
        Shard(
            filename="00-overview.md",
            title="TAD — Document Meta, Architecture Overview, and Summary",
            sections=[1, 2, 23],
            description="Document meta, architecture overview including system shape and principles, and executive summary.",
        ),
        Shard(
            filename="01-component-architecture.md",
            title="TAD — Component Architecture",
            sections=[3],
            description="Frontend stack and state structure, Python sidecar process model and module structure, repo layout, build and distribution.",
        ),
        Shard(
            filename="02-data-model.md",
            title="TAD — Data Model",
            sections=[4],
            description="Pydantic v2 schemas for all 13 core entities, SQLite schema philosophy, project folder layout, migrations, and TypeScript codegen.",
        ),
        Shard(
            filename="03-ipc-architecture.md",
            title="TAD — IPC Architecture",
            sections=[5],
            description="JSON-RPC 2.0 over stdio protocol, message categories, method naming, error handling, progress events, admin gating.",
        ),
        Shard(
            filename="04-pipelines.md",
            title="TAD — Pipeline Architecture",
            sections=[6],
            description="Every generation stage: collection planning, per-item spec, texture gen, thumbnail render, metadata, validation, DBPF packaging, auto-install, verification.",
        ),
        Shard(
            filename="05-ai-orchestration.md",
            title="TAD — AI Orchestration Layer",
            sections=[7],
            description="Model assignments, client wrappers, prompt library, cost tracking, determinism notes.",
        ),
        Shard(
            filename="06-archetype-handlers.md",
            title="TAD — Archetype Handlers",
            sections=[8],
            description="Common handler interface, per-archetype implementation notes (light, audio, mirror, moodlet), curated moodlet list.",
        ),
        Shard(
            filename="07-template-library.md",
            title="TAD — Template Library Implementation",
            sections=[9],
            description="Template registry, storage layout, manifest format, Tier 2 importer, Tier 2 → Tier 1 promotion, graceful degradation.",
        ),
        Shard(
            filename="08-dbpf-packaging.md",
            title="TAD — DBPF Packaging",
            sections=[10],
            description="Library boundary, deterministic TGI ID generation, resource types produced, DDS encoding, catalog entry construction, custom filter tags.",
        ),
        Shard(
            filename="09-tuning-clone.md",
            title="TAD — Tuning Clone Pipeline",
            sections=[11],
            description="Extraction from local Sims install, tuning parsing, clone operation, targeted edits, validation of cloned tuning.",
        ),
        Shard(
            filename="10-validation.md",
            title="TAD — Validation Engine",
            sections=[12],
            description="Structure, check categories, execution, user and admin messaging.",
        ),
        Shard(
            filename="11-install.md",
            title="TAD — Auto-Install Mechanism",
            sections=[13],
            description="Mods folder detection, pre-install checks, conflict handling, atomicity, script mods detection.",
        ),
        Shard(
            filename="12-admin-mode.md",
            title="TAD — Admin Mode Architecture",
            sections=[14],
            description="Gating, admin endpoints, admin UI architecture, admin-only features.",
        ),
        Shard(
            filename="13-cross-platform.md",
            title="TAD — Cross-Platform Considerations",
            sections=[15],
            description="Path resolution per platform, file encoding, Blender invocation, subprocess handling, parity testing.",
        ),
        Shard(
            filename="14-errors-logging.md",
            title="TAD — Error Handling, Logging, and Observability",
            sections=[16],
            description="Error taxonomy, error flow, structured logging, observable events, no-telemetry policy.",
        ),
        Shard(
            filename="15-security.md",
            title="TAD — Security and Privacy Implementation",
            sections=[17],
            description="Network access scope, credential storage in platform keyrings, file system access boundaries, process isolation, user data handling.",
        ),
        Shard(
            filename="16-testing-and-deployment.md",
            title="TAD — Testing, Dependencies, Deployment, and Boundaries",
            sections=[18, 19, 20, 21, 22],
            description="Testing architecture, dependency inventory, build and deployment, open technical questions, architectural boundaries of the TAD itself.",
        ),
    ],
)


# --------------------------------------------------------------------------- #
# API shards
# --------------------------------------------------------------------------- #
API = SourceDoc(
    monolithic_filename="API_Specification.md",
    output_subdir="api",
    area_label="API Spec",
    shards=[
        Shard(
            filename="00-overview.md",
            title="API Spec — Document Meta, Protocol, Types, and Summary",
            sections=[1, 2, 3, 23],
            description="Document meta, JSON-RPC 2.0 protocol basics, type conventions and common enums, executive summary.",
        ),
        Shard(
            filename="01-system.md",
            title="API Spec — system.* Namespace",
            sections=[4],
            description="system.version, system.shutdown, system.health, system.paths, system.set_admin_mode, system.open_external_path.",
        ),
        Shard(
            filename="02-config.md",
            title="API Spec — config.* Namespace",
            sections=[5],
            description="config.get, config.set, config.set_api_key, config.clear_api_key, config.redetect_paths.",
        ),
        Shard(
            filename="03-project.md",
            title="API Spec — project.* Namespace",
            sections=[6],
            description="project.create, project.open, project.close, project.list_recent, project.rename, project.delete, project.get.",
        ),
        Shard(
            filename="04-collection.md",
            title="API Spec — collection.* Namespace",
            sections=[7],
            description="collection.create, collection.plan, collection.update_plan, collection.approve_plan, collection.generate, collection.cancel, collection.get.",
        ),
        Shard(
            filename="05-item.md",
            title="API Spec — item.* Namespace",
            sections=[8],
            description="item.get, item.regenerate, item.replace, item.exclude, item.include, item.update_metadata, item.set_primary_swatch.",
        ),
        Shard(
            filename="06-swatch.md",
            title="API Spec — swatch.* Namespace",
            sections=[9],
            description="swatch.regenerate, swatch.delete, swatch.add.",
        ),
        Shard(
            filename="07-functional.md",
            title="API Spec — functional.* Namespace",
            sections=[10],
            description="functional.list_compatible_archetypes, functional.available_moodlets, functional.preview, functional.create, functional.update, functional.delete.",
        ),
        Shard(
            filename="08-validation.md",
            title="API Spec — validation.* Namespace",
            sections=[11],
            description="validation.run.",
        ),
        Shard(
            filename="09-export.md",
            title="API Spec — export.* Namespace",
            sections=[12],
            description="export.run, export.retry_install, export.resolve_conflict, export.list_artifacts.",
        ),
        Shard(
            filename="10-verification.md",
            title="API Spec — verification.* Namespace",
            sections=[13],
            description="verification.mark_item, verification.mark_collection, verification.get.",
        ),
        Shard(
            filename="11-templates.md",
            title="API Spec — templates.* Namespace",
            sections=[14],
            description="templates.list, templates.get.",
        ),
        Shard(
            filename="12-admin.md",
            title="API Spec — admin.* Namespace (admin-mode-gated)",
            sections=[15],
            description="admin.template.*, admin.logs.*, admin.jobs.*, admin.reference.*, admin.rebuild, admin.cost_summary.",
        ),
        Shard(
            filename="13-notifications.md",
            title="API Spec — Notifications",
            sections=[16],
            description="All sidecar-to-frontend notifications: progress, status changes, conflicts, log events, errors, sidecar ready.",
        ),
        Shard(
            filename="14-error-codes.md",
            title="API Spec — Error Codes",
            sections=[17],
            description="Complete enum of error codes organized by category.",
        ),
        Shard(
            filename="15-protocol-details.md",
            title="API Spec — Concurrency, Versioning, Examples, and Implementation Notes",
            sections=[18, 19, 20, 21, 22],
            description="Concurrency and rate limiting, versioning and backward compatibility, full flow examples, implementation notes for Claude Code, and open method-level items.",
        ),
    ],
)


# --------------------------------------------------------------------------- #
# Diagrams shards
# --------------------------------------------------------------------------- #
DIAGRAMS = SourceDoc(
    monolithic_filename="Architecture_Diagrams.md",
    output_subdir="diagrams",
    area_label="Diagrams",
    shards=[
        Shard(
            filename="00-overview.md",
            title="Diagrams — Document Meta, Conventions, Index, and Maintenance",
            sections=[1, 2, 14, 15],
            description="Document meta, shape/arrow/color conventions, full diagram index, maintenance notes.",
        ),
        Shard(
            filename="01-system-architecture.md",
            title="Diagrams — System Architecture",
            sections=[3],
            description="Container diagram, sidecar internal components, frontend components, deployment topology.",
        ),
        Shard(
            filename="02-data-architecture.md",
            title="Diagrams — Data Architecture",
            sections=[4],
            description="Core entity-relationship diagram and project folder layout tree.",
        ),
        Shard(
            filename="03-pipelines.md",
            title="Diagrams — Pipeline Sequence Diagrams",
            sections=[5],
            description="Project creation, collection generation, per-item regen, functional overlay, validation and export, deterministic rebuild, IPC message flow.",
        ),
        Shard(
            filename="04-state-machines.md",
            title="Diagrams — State Machines",
            sections=[6],
            description="Item, Collection, BuildJob, Swatch, and FunctionalOverlay lifecycles.",
        ),
        Shard(
            filename="05-template-library.md",
            title="Diagrams — Template Library Architecture",
            sections=[7],
            description="Tier structure and promotion flow, template resolution path.",
        ),
        Shard(
            filename="06-ai-orchestration.md",
            title="Diagrams — AI Stage Orchestration",
            sections=[8],
            description="AI stage input/output overview and retry/failure handling.",
        ),
        Shard(
            filename="07-admin-mode.md",
            title="Diagrams — Admin Mode Architecture",
            sections=[9],
            description="Admin mode access gating state diagram and admin operations inventory.",
        ),
        Shard(
            filename="08-error-flow.md",
            title="Diagrams — Error Flow",
            sections=[10],
            description="Error propagation and messaging from failure to creator/admin UI.",
        ),
        Shard(
            filename="09-phase-deps.md",
            title="Diagrams — MVP Phase Dependencies",
            sections=[11],
            description="Phase sequence and gates, and a representative intra-phase task dependency graph (Phase 3).",
        ),
        Shard(
            filename="10-cross-platform-security.md",
            title="Diagrams — Cross-Platform and Security Boundaries",
            sections=[12, 13],
            description="Cross-platform path resolution per OS, data trust boundaries, file system access permissions.",
        ),
    ],
)


# --------------------------------------------------------------------------- #
# MVP phase sections need special handling — they are subsections of §9.
# We parse them from the monolithic MVP spec directly.
# --------------------------------------------------------------------------- #
MVP_PHASE_MAPPING = [
    ("05-phase-0-foundation.md", "Phase 0 — Foundation", "9.1"),
    ("06-phase-1-poc.md", "Phase 1 — Milestone Zero: Texturing Proof-of-Concept", "9.2"),
    ("07-phase-2-templates.md", "Phase 2 — Template Library", "9.3"),
    ("08-phase-3-decorative.md", "Phase 3 — Decorative Generation Pipeline", "9.4"),
    ("09-phase-4-validation-export.md", "Phase 4 — Validation, Export, and Auto-Install", "9.5"),
    ("10-phase-5-functional.md", "Phase 5 — Functional Overlay", "9.6"),
    ("11-phase-6-admin.md", "Phase 6 — Admin Mode", "9.7"),
    ("12-phase-7-polish.md", "Phase 7 — Cross-Platform Hardening and Polish", "9.8"),
]

PHASE_SUBSECTION_RE = re.compile(
    r"^### 9\.(\d+)\s+(.+?)$(.*?)(?=^### 9\.\d+\s+|^## \d+\.\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)


def shard_mvp_phases(root: Path, phase_shards: list[Shard]) -> list[Path]:
    """Split MVP spec §9 into one file per phase (§9.1–§9.8)."""
    mono_path = root / "docs" / "MONOLITHIC" / "MVP_Specification.md"
    content = mono_path.read_text(encoding="utf-8")

    # Extract the top-level §9 body so we can find subsections
    sections = parse_sections(content)
    if 9 not in sections:
        raise ValueError("MVP spec is missing §9")
    _, section_9_body = sections[9]

    phase_matches = list(PHASE_SUBSECTION_RE.finditer(section_9_body))
    phase_bodies: dict[str, tuple[str, str]] = {}
    for match in phase_matches:
        sub_num = f"9.{match.group(1)}"
        title = match.group(2).strip()
        # Body only (top-level shard header already has the title)
        body = match.group(3).strip() + "\n"
        phase_bodies[sub_num] = (title, body)

    out_dir = root / "docs" / "mvp"
    produced: list[Path] = []

    for filename, shard_title, subsection in MVP_PHASE_MAPPING:
        if subsection not in phase_bodies:
            raise ValueError(f"MVP phase {subsection} not found in monolithic doc")
        title_for_shard = f"MVP Spec — {shard_title}"
        _, body = phase_bodies[subsection]

        # Find the matching Shard object for its description
        shard = next(s for s in phase_shards if s.filename == filename)

        lines: list[str] = []
        lines.append(f"# {title_for_shard}\n")
        lines.append(
            f"> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · "
            f"**Area:** MVP Spec · "
            f"**Sections:** §{subsection}\n"
        )
        lines.append(f"> {shard.description}\n")
        lines.append("---\n")
        lines.append(body)

        out_path = out_dir / filename
        out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        produced.append(out_path)

    return produced


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    all_produced: list[Path] = []

    # MVP phases need special handling because they're subsections of §9.
    # Other MVP shards use the normal flow. We filter phase shards out of
    # the MVP doc before running the generic sharder.
    phase_filenames = {name for name, _, _ in MVP_PHASE_MAPPING}
    mvp_non_phase_shards = [s for s in MVP.shards if s.filename not in phase_filenames]
    mvp_phase_shards = [s for s in MVP.shards if s.filename in phase_filenames]

    mvp_non_phase = SourceDoc(
        monolithic_filename=MVP.monolithic_filename,
        output_subdir=MVP.output_subdir,
        area_label=MVP.area_label,
        shards=mvp_non_phase_shards,
    )

    for doc in [PRD, mvp_non_phase, TAD, API, DIAGRAMS]:
        produced = shard_doc(doc, ROOT)
        all_produced.extend(produced)
        print(f"Sharded {doc.monolithic_filename} into {len(produced)} files")

    # Shard MVP phases
    produced = shard_mvp_phases(ROOT, mvp_phase_shards)
    all_produced.extend(produced)
    print(f"Sharded MVP phases into {len(produced)} files")

    print(f"\nTotal shards produced: {len(all_produced)}")


if __name__ == "__main__":
    main()

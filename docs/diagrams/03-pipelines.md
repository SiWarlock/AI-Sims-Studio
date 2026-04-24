# Diagrams — Pipeline Sequence Diagrams

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §5

> Project creation, collection generation, per-item regen, functional overlay, validation and export, deterministic rebuild, IPC message flow.

---

## 5. Pipeline Sequence Diagrams

### 5.1 Project Creation and Collection Planning

From the user entering a prompt to an approved plan ready for generation.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant IPC as IPC Layer
    participant SC as Sidecar Core
    participant Store as Storage
    participant Tpl as Template Registry
    participant Plan as Planning Stage
    participant Claude as Anthropic API

    User->>FE: Enter name, prompt, size, style
    FE->>IPC: project.create(params)
    IPC->>SC: route to project handler
    SC->>Store: create project + collection records
    Store-->>SC: records persisted
    SC-->>IPC: project_id, collection_id
    IPC-->>FE: response
    FE->>User: Navigate to plan review

    User->>FE: Trigger plan generation
    FE->>IPC: collection.plan(collection_id)
    IPC->>SC: route
    SC->>Tpl: get registry snapshot
    Tpl-->>SC: 19 templates with schemas
    SC->>Plan: run(PlanningInput)
    Plan->>Claude: tool-use request with CollectionPlan schema
    Claude-->>Plan: structured plan response
    Plan-->>SC: CollectionPlan
    SC->>Store: persist plan to collection
    Store-->>SC: OK
    SC-.->IPC: generation.progress events
    IPC-.->FE: progress events
    SC-->>IPC: plan complete
    IPC-->>FE: final plan
    FE->>User: Display plan with confidence scores
```

### 5.2 Collection Generation (Main Pipeline)

After plan approval, the full generation flow across all items and swatches.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant SC as Sidecar Core
    participant Jobs as Job Scheduler
    participant Spec as Spec Gen Stage
    participant Tex as Texture Gen Stage
    participant Thumb as Thumbnail Stage
    participant Store as Storage
    participant Claude as Anthropic API
    participant Rep as Replicate API
    participant Blend as Blender Subprocess

    User->>FE: Approve plan, start generation
    FE->>SC: collection.generate(collection_id)
    SC->>Jobs: schedule collection job
    Jobs->>Jobs: spawn parallel per-item tasks

    par Per item (parallel)
        Jobs->>Spec: run(SpecInput)
        Spec->>Claude: tool-use for ItemSpec
        Claude-->>Spec: ItemSpec
        Spec-->>Jobs: spec ready
        Jobs->>Store: persist ItemSpec
        Jobs-.->FE: item status: generated (spec)
    end

    par Per swatch per item (bounded parallel, cap 4)
        Jobs->>Tex: run(TextureGenInput)
        loop Per texture zone
            Tex->>Rep: diffuse generation
            Rep-->>Tex: diffuse PNG
            Tex->>Rep: normal / specular generation (or derived)
            Rep-->>Tex: normal / specular PNGs
        end
        Tex-->>Jobs: TextureSet
        Jobs->>Store: persist TextureSet, save PNGs to disk
        Jobs-.->FE: swatch status: generated
    end

    loop Per item (serial, Blender lock)
        Jobs->>Thumb: run(ThumbnailInput)
        Thumb->>Blend: invoke with job spec
        Blend-->>Thumb: thumbnail PNGs
        Thumb-->>Jobs: paths
        Jobs->>Store: persist thumbnail paths
        Jobs-.->FE: item status: generated (complete)
    end

    Jobs-->>SC: collection complete
    SC-->>FE: generation.complete
    FE->>User: Display collection board
```

### 5.3 Per-Item Regeneration

Isolated regeneration of a single item without affecting others.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant SC as Sidecar Core
    participant Tex as Texture Gen
    participant Thumb as Thumbnail
    participant Store as Storage

    User->>FE: Click "Regenerate" on item
    FE->>SC: item.regenerate(item_id)
    SC->>Store: mark item as regenerating, archive old textures
    SC->>Tex: new texture generation (same spec, new seed)
    Tex-->>SC: new TextureSet
    SC->>Thumb: new thumbnail render
    Thumb-->>SC: new thumbnail
    SC->>Store: persist new artifacts
    SC-.->FE: item status events
    SC-->>FE: regeneration complete
    FE->>User: Updated item in UI
```

### 5.4 Functional Overlay Creation

Upgrading a decor item to a functional object.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant SC as Sidecar Core
    participant Arch as Archetype Handler
    participant SimsInst as Sims Install Reader
    participant Tun as Tuning Module
    participant Store as Storage

    User->>FE: Click "Make Functional" on item
    FE->>SC: functional.list_compatible(item_id)
    SC->>Store: load item + template
    SC->>Arch: filter archetypes by template compatibility
    SC-->>FE: list of compatible archetypes
    FE->>User: Show archetype selection

    User->>FE: Select archetype, configure
    FE->>SC: functional.preview(item_id, archetype, config)
    SC->>Arch: validate configuration
    Arch-->>SC: valid
    SC->>Arch: generate summary
    Arch-->>SC: human-readable summary
    SC-->>FE: summary
    FE->>User: Show confirmation

    User->>FE: Confirm
    FE->>SC: functional.create(item_id, archetype, config)
    SC->>SimsInst: extract reference object tuning
    SimsInst-->>SC: tuning XML bytes
    SC->>Tun: parse tuning
    Tun-->>SC: typed tuning tree
    SC->>Arch: build_overlay(item, template, config, ref_resources)
    Arch->>Tun: clone and apply targeted edits
    Tun-->>Arch: modified tuning
    Arch-->>SC: BuiltOverlay
    SC->>Store: persist FunctionalOverlay record
    SC-->>FE: overlay created
    FE->>User: Show functional status in item detail
```

### 5.5 Validation and Export

From pre-export validation to auto-install.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant SC as Sidecar Core
    participant Val as Validation Engine
    participant Pkg as Packaging Module
    participant DBPF as DBPF Library
    participant Inst as Install Module
    participant Store as Storage
    participant Mods as Mods Folder

    User->>FE: Open export screen
    FE->>SC: validation.run(collection_id)
    SC->>Val: validate(collection_id)
    Val->>Store: load collection state
    Val->>Val: run all checks in parallel
    Val-->>SC: ValidationResult
    SC-->>FE: errors, warnings, per-item status
    FE->>User: Show validation summary

    User->>FE: Resolve issues, pick variants, trigger export
    FE->>SC: export.run(collection_id, variant_choices)
    SC->>Pkg: build_package(collection, choices)

    loop Per included item
        Pkg->>Pkg: encode textures to DDS
        Pkg->>Pkg: build catalog entry
        Pkg->>Pkg: build string table
        alt Functional variant
            Pkg->>Pkg: add cloned tuning resources
        end
        Pkg->>DBPF: add_resource(TGI, data)
    end

    Pkg->>DBPF: close
    DBPF-->>Pkg: .package file written
    Pkg-->>SC: ExportArtifact
    SC->>Store: persist artifact record

    SC->>Inst: auto_install(artifact)
    Inst->>Inst: detect Mods folder, check conflicts
    alt Conflict detected
        Inst-.->FE: prompt user (overwrite / rename / skip)
        FE-->>Inst: user choice
    end
    Inst->>Mods: atomic copy .package
    Mods-->>Inst: OK
    Inst-->>SC: install_path
    SC->>Store: update artifact with install_path
    SC-->>FE: export complete

    FE->>User: Show success, offer verification flow
```

### 5.6 Deterministic Rebuild

The admin-triggered rebuild pathway that produces byte-identical output.

```mermaid
sequenceDiagram
    actor Admin
    participant FE as Admin Frontend
    participant SC as Sidecar Core
    participant Store as Storage
    participant Pkg as Packaging
    participant DBPF as DBPF Library

    Admin->>FE: Admin Mode > Rebuild Project
    FE->>SC: admin.rebuild(project_id)
    SC->>Store: load full project state
    SC->>Pkg: build_package with deterministic TGI generation
    Pkg->>DBPF: emit resources in canonical order
    DBPF-->>Pkg: .package file
    Pkg->>Pkg: compute SHA-256
    Pkg-->>SC: new ExportArtifact
    SC->>SC: compare SHA-256 with prior artifact if exists
    SC-->>FE: rebuild result (identical? differences?)
    FE->>Admin: Display parity verification
```

### 5.7 IPC Message Flow

Request-response and notification pattern over stdio.

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant Stdin as sidecar stdin
    participant SC as Sidecar
    participant Stdout as sidecar stdout

    Note over FE,Stdout: Request-Response
    FE->>Stdin: {"jsonrpc":"2.0","id":"r1","method":"project.create","params":{...}}
    Stdin->>SC: parse & dispatch
    SC->>SC: execute handler
    SC->>Stdout: {"jsonrpc":"2.0","id":"r1","result":{...}}
    Stdout->>FE: resolve promise

    Note over FE,Stdout: Progress Notifications (no id)
    SC-.->Stdout: {"jsonrpc":"2.0","method":"generation.progress","params":{...}}
    Stdout-.->FE: dispatch to Redux

    Note over FE,Stdout: Error Response
    FE->>Stdin: {"jsonrpc":"2.0","id":"r2","method":"collection.generate",...}
    SC->>Stdout: {"jsonrpc":"2.0","id":"r2","error":{"code":-32000,"data":{...}}}
    Stdout->>FE: reject promise with structured error
```

---

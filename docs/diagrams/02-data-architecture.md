# Diagrams — Data Architecture

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §4

> Core entity-relationship diagram and project folder layout tree.

---

## 4. Data Architecture

### 4.1 Core Entity Relationships

Entity-relationship view of the primary persisted domain model.

```mermaid
erDiagram
    PROJECT ||--o{ COLLECTION : "contains"
    PROJECT ||--o{ REFERENCE_INPUT : "has"
    COLLECTION ||--o{ ITEM : "contains"
    ITEM ||--|| ITEM_METADATA : "has"
    ITEM ||--o| ITEM_SPEC : "generated"
    ITEM ||--o{ SWATCH : "has"
    ITEM ||--o| FUNCTIONAL_OVERLAY : "upgraded to"
    SWATCH ||--|| TEXTURE_SET : "has"
    TEXTURE_SET ||--o{ ZONE_MAPS : "contains per zone"
    ITEM }o--|| TEMPLATE : "built from"
    FUNCTIONAL_OVERLAY }o--|| ARCHETYPE : "uses"
    ARCHETYPE }o--|| REFERENCE_OBJECT : "clones"
    COLLECTION ||--o{ BUILD_JOB : "produces"
    COLLECTION ||--o{ VALIDATION_RESULT : "validated by"
    COLLECTION ||--o{ EXPORT_ARTIFACT : "exports to"
    BUILD_JOB ||--o{ GENERATION_ATTEMPT : "records"
    VALIDATION_RESULT ||--o{ VALIDATION_ISSUE : "contains"
    EXPORT_ARTIFACT }o--|| COLLECTION : "packages"

    PROJECT {
        uuid id PK
        string name
        string theme_prompt
        datetime created_at
        datetime updated_at
        int schema_version
    }
    COLLECTION {
        uuid id PK
        uuid project_id FK
        string name
        enum style_preference
        int target_item_count
        enum mode
        enum status
    }
    ITEM {
        uuid id PK
        uuid collection_id FK
        int order_index
        string source_request
        string template_id FK
        float template_match_confidence
        bool included_in_export
        enum status
    }
    SWATCH {
        uuid id PK
        uuid item_id FK
        int index
        uuid texture_set_id FK
        enum status
    }
    FUNCTIONAL_OVERLAY {
        uuid id PK
        uuid item_id FK
        enum archetype
        json configuration
        string reference_object_id
        enum status
    }
    TEMPLATE {
        string id PK
        enum tier
        string shape_class
        enum footprint_type
        json texture_zones
        int schema_version
    }
```

### 4.2 Project Folder Layout

Directory tree showing how a single project is stored on disk.

```mermaid
graph TB
    Root["projects/{project_name}/"]
    Root --> DB["project.sqlite"]
    Root --> Assets["assets/"]
    Root --> Exports["exports/"]
    Root --> ProjectLogs["logs/"]

    Assets --> Thumbs["thumbnails/<br/>{item_id}.png<br/>{item_id}_swatch_{index}.png"]
    Assets --> Textures["textures/<br/>{swatch_id}/<br/>  {zone}_diffuse.png<br/>  {zone}_normal.png<br/>  {zone}_specular.png"]
    Assets --> Refs["references/<br/>{reference_id}.{ext}"]

    Exports --> ExportDir["{export_id}/<br/>{collection_name}.package<br/>export_manifest.json"]

    ProjectLogs --> SessionLog["session_{timestamp}.log"]

    classDef folder fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000
    class Root,Assets,Exports,ProjectLogs,Thumbs,Textures,Refs,ExportDir,SessionLog folder
    classDef file fill:#fff3e0,stroke:#f57c00,stroke-width:1px,color:#000
    class DB file
```

---

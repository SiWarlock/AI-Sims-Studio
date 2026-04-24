# Diagrams — Template Library Architecture

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §7

> Tier structure and promotion flow, template resolution path.

---

## 7. Template Library Architecture

### 7.1 Tier Structure and Promotion Flow

How templates exist in two tiers and move between them.

```mermaid
graph TB
    subgraph T1["Tier 1 — Curated (shipped with app)"]
        T1Decor["Decor Primitives (11)<br/>cylindrical, boxy, rectangular, etc."]
        T1Furn["Furniture Primitives (8)<br/>seating, beds, tables, storage"]
    end

    subgraph T2["Tier 2 — User-Imported"]
        T2Raw["Base-game meshes<br/>partial schema"]
    end

    subgraph Sims["User's Sims 4 Install"]
        BaseObjs["Base-game objects<br/>(read-only source)"]
    end

    subgraph Flow["Workflow"]
        AdminImport["Admin: Import Mesh"]
        AdminPromote["Admin: Author Schema<br/>and Promote"]
    end

    subgraph Usage["Usage by Planning Stage"]
        PlanningStage["AI reasons over<br/>all Tier 1 + promoted Tier 2"]
    end

    BaseObjs -.-> AdminImport
    AdminImport --> T2Raw
    T2Raw -.-> AdminPromote
    AdminPromote --> T1Decor
    AdminPromote --> T1Furn

    T1Decor --> PlanningStage
    T1Furn --> PlanningStage
    T2Raw -.->|decorative only| PlanningStage

    classDef tier1 fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef tier2 fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000
    classDef external fill:#eceff1,stroke:#546e7a,stroke-width:2px,color:#000
    classDef workflow fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef usage fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#000

    class T1Decor,T1Furn tier1
    class T2Raw tier2
    class BaseObjs external
    class AdminImport,AdminPromote workflow
    class PlanningStage usage
```

### 7.2 Template Resolution Path

How the planning stage turns a user's request into a template choice.

```mermaid
graph LR
    UserReq["User request:<br/>'Y2K CD player'"]
    ClaudeReason["Claude reasons over<br/>template schemas"]
    Registry["Template Registry<br/>19 Tier 1 + N Tier 2"]
    Match["Best match:<br/>boxy_electronic_small_tabletop"]
    Confidence["Confidence: 0.89"]

    UserReq --> ClaudeReason
    Registry --> ClaudeReason
    ClaudeReason --> Match
    ClaudeReason --> Confidence

    Match --> Decision{"Confidence<br/>above threshold?"}
    Confidence --> Decision
    Decision -->|Yes| Proceed["Add to plan"]
    Decision -->|No| Warn["Flag with warning<br/>for user review"]

    classDef input fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000
    classDef ai fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef data fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000
    classDef outcome fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef warning fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000

    class UserReq input
    class ClaudeReason,Match,Confidence ai
    class Registry data
    class Proceed outcome
    class Warn warning
```

---

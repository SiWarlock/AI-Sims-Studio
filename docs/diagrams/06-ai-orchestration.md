# Diagrams — AI Stage Orchestration

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §8

> AI stage input/output overview and retry/failure handling.

---

## 8. AI Stage Orchestration

### 8.1 AI Stage Input / Output Overview

Where AI touches the system and what flows through each stage.

```mermaid
graph TB
    UserPrompt["User prompt +<br/>desired item count"]

    subgraph Stage1["Stage 1: Collection Planning"]
        PlanIn["PlanningInput<br/>(prompt, count, registry, style)"]
        Sonnet1["Claude Sonnet 4.6<br/>(tool use: submit_plan)"]
        PlanOut["CollectionPlan<br/>(items, template IDs, confidence)"]
    end

    subgraph Stage2["Stage 2: Per-Item Spec (parallel)"]
        SpecIn["SpecInput<br/>(request, template schema, collection ctx)"]
        Sonnet2["Claude Sonnet 4.6<br/>(tool use: submit_item_spec)"]
        SpecOut["ItemSpec<br/>(zone prompts, metadata)"]
    end

    subgraph Stage3["Stage 3: Texture Gen (parallel per swatch per zone)"]
        TexIn["TextureGenInput<br/>(zone prompts, template)"]
        Image["Replicate Image Model<br/>(Flux or alternative)"]
        TexOut["TextureSet<br/>(diffuse, normal, specular PNGs)"]
    end

    subgraph Deterministic["Deterministic Stages (no AI)"]
        Thumb["Blender thumbnail render"]
        DBPFBuild["DBPF packaging"]
        TuningClone["Tuning clone"]
        Validate["Validation"]
    end

    subgraph Support["Supporting AI Uses"]
        HaikuRewrite["Claude Haiku 4.5<br/>validation message rewriting"]
        HaikuRephrase["Claude Haiku 4.5<br/>content policy retry rephrase"]
        SonnetRepair["Claude Sonnet 4.6<br/>repair suggestions"]
        SonnetTuning["Claude Sonnet 4.6<br/>tuning value suggestions"]
    end

    UserPrompt --> PlanIn
    PlanIn --> Sonnet1
    Sonnet1 --> PlanOut

    PlanOut --> SpecIn
    SpecIn --> Sonnet2
    Sonnet2 --> SpecOut

    SpecOut --> TexIn
    TexIn --> Image
    Image --> TexOut

    TexOut --> Thumb
    Thumb --> DBPFBuild
    SonnetTuning -.-> TuningClone
    TuningClone --> DBPFBuild
    DBPFBuild --> Validate

    Validate -.-> HaikuRewrite
    Image -.-> HaikuRephrase
    Validate -.-> SonnetRepair

    classDef input fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000
    classDef ai fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef det fill:#b2dfdb,stroke:#00796b,stroke-width:2px,color:#000
    classDef output fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000

    class UserPrompt,PlanIn,SpecIn,TexIn input
    class Sonnet1,Sonnet2,Image,HaikuRewrite,HaikuRephrase,SonnetRepair,SonnetTuning ai
    class Thumb,DBPFBuild,TuningClone,Validate det
    class PlanOut,SpecOut,TexOut output
```

### 8.2 Retry and Failure Handling Per Stage

```mermaid
graph TB
    Start["Stage begins"]
    Attempt["Execute primary call"]
    Check{"Success?"}
    Retry{"Retriable?<br/>Under retry cap?"}
    Backoff["Exponential backoff<br/>1s → 4s → 16s"]
    Fallback{"Stage-specific<br/>fallback?"}
    Rephrase["Haiku rephrase<br/>(content policy)"]
    Success["Return output"]
    FailItem["Mark target entity<br/>needs-review / error"]
    Surface["Surface structured error<br/>to user"]

    Start --> Attempt
    Attempt --> Check
    Check -->|Yes| Success
    Check -->|No| Retry
    Retry -->|Yes| Backoff
    Backoff --> Attempt
    Retry -->|No| Fallback
    Fallback -->|Content policy| Rephrase
    Rephrase --> Attempt
    Fallback -->|None applicable| FailItem
    FailItem --> Surface

    classDef ok fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef fail fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000
    classDef action fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000

    class Success ok
    class FailItem,Surface fail
    class Check,Retry,Fallback decision
    class Start,Attempt,Backoff,Rephrase action
```

---

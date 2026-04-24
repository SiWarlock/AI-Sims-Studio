# Diagrams — System Architecture

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §3

> Container diagram, sidecar internal components, frontend components, deployment topology.

---

## 3. System Architecture

### 3.1 Container Diagram

Top-level view: what processes exist, who talks to whom, and where data crosses process boundaries.

```mermaid
graph TB
    User((Creator / Admin))

    subgraph Desktop["Desktop Application (macOS or Windows)"]
        subgraph Tauri["Tauri Host Process"]
            Frontend["React Frontend<br/>(Redux Toolkit, Tailwind)"]
        end

        subgraph Python["Python Sidecar Process"]
            Sidecar["asyncio Event Loop<br/>JSON-RPC Server<br/>Pipeline Orchestrator"]
        end

        Frontend <-. "JSON-RPC 2.0<br/>over stdio" .-> Sidecar
    end

    subgraph LocalFS["User's Local File System"]
        ProjectStore[("Projects<br/>SQLite + Assets")]
        Logs[("Logs")]
        Config[("Config")]
        TemplateLib[("Tier 1 Template Library<br/>bundled with app")]
        Tier2Lib[("Tier 2 Template Library<br/>user-imported")]
    end

    subgraph External["External Systems"]
        AnthropicAPI{{"Anthropic API<br/>Claude Sonnet / Haiku"}}
        ReplicateAPI{{"Replicate API<br/>Image Generation"}}
        Blender{{"Blender<br/>(subprocess)"}}
        SimsInstall[("Sims 4 Installation<br/>read-only")]
        ModsFolder[("Sims 4 Mods Folder<br/>write")]
    end

    User ==> Frontend

    Sidecar --> ProjectStore
    Sidecar --> Logs
    Sidecar --> Config
    Sidecar --> TemplateLib
    Sidecar --> Tier2Lib

    Sidecar --> AnthropicAPI
    Sidecar --> ReplicateAPI
    Sidecar --> Blender
    Sidecar --> SimsInstall
    Sidecar --> ModsFolder

    classDef frontend fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000
    classDef sidecar fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef external fill:#eceff1,stroke:#546e7a,stroke-width:2px,color:#000
    classDef datastore fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000
    classDef userNode fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#000

    class Frontend frontend
    class Sidecar sidecar
    class AnthropicAPI,ReplicateAPI,Blender,SimsInstall,ModsFolder external
    class ProjectStore,Logs,Config,TemplateLib,Tier2Lib datastore
    class User userNode
```

### 3.2 Sidecar Internal Component Diagram

Modules inside the Python sidecar and how they compose.

```mermaid
graph TB
    IPC["ipc/<br/>JSON-RPC Server"]

    subgraph Orchestration["Orchestration Layer"]
        Jobs["jobs/<br/>Async Scheduler"]
        Errors["errors/<br/>Error Taxonomy"]
    end

    subgraph Pipelines["Generation Pipelines"]
        Planning["planning/<br/>Collection Planning"]
        SpecGen["spec_gen/<br/>Item Spec Generation"]
        TextureGen["texture_gen/<br/>Texture Generation"]
        Thumbnail["thumbnail/<br/>Blender Render"]
        Assembly["assembly/<br/>Textured Asset Assembly"]
    end

    subgraph Packaging["Packaging & Validation"]
        DBPFLib["dbpf_lib/<br/>DBPF Adapter"]
        PkgMod["packaging/<br/>Package Builder"]
        Tuning["tuning/<br/>Tuning Parser & Editor"]
        Archetypes["archetypes/<br/>Light / Audio / Mirror / Moodlet"]
        Validation["validation/<br/>Validation Engine"]
    end

    subgraph Supporting["Supporting Modules"]
        Storage["storage/<br/>SQLite Access"]
        Templates["templates/<br/>Registry & Loader"]
        SimsInstallMod["sims_install/<br/>Read-only Extraction"]
        Install["install/<br/>Mods Folder Copy"]
        Config["config/<br/>Paths & Platform"]
        Schemas["schemas/<br/>Pydantic Models"]
        Logging["logging_setup/"]
        Admin["admin/<br/>Admin Operations"]
    end

    IPC --> Jobs
    IPC --> Admin
    Jobs --> Planning
    Jobs --> SpecGen
    Jobs --> TextureGen
    Jobs --> Thumbnail
    Jobs --> Assembly
    Jobs --> PkgMod
    Jobs --> Validation
    Jobs --> Install

    Planning --> Schemas
    SpecGen --> Schemas
    TextureGen --> Schemas
    Thumbnail --> Schemas

    Assembly --> Templates
    Assembly --> TextureGen
    PkgMod --> DBPFLib
    PkgMod --> Tuning
    PkgMod --> Archetypes
    Archetypes --> SimsInstallMod
    Archetypes --> Tuning
    Validation --> Storage
    Validation --> DBPFLib

    Storage --> Schemas
    Templates --> Schemas
    SimsInstallMod --> DBPFLib

    Admin --> Templates
    Admin --> SimsInstallMod
    Admin --> Storage

    Errors -.-> IPC
    Logging -.-> IPC
    Config -.-> Storage
    Config -.-> SimsInstallMod
    Config -.-> Install

    classDef pipeline fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef deterministic fill:#b2dfdb,stroke:#00796b,stroke-width:2px,color:#000
    classDef support fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef infra fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000

    class Planning,SpecGen,TextureGen pipeline
    class Thumbnail,Assembly,PkgMod,DBPFLib,Tuning,Archetypes,Validation,Install deterministic
    class Storage,Templates,SimsInstallMod,Schemas,Config,Logging,Admin support
    class IPC,Jobs,Errors infra
```

### 3.3 Frontend Component Diagram

React application structure, including Redux slices, screens, and the IPC client.

```mermaid
graph TB
    subgraph FrontendApp["React Frontend"]
        Router["React Router<br/>(memory mode)"]

        subgraph Store["Redux Store"]
            ProjectSlice["projectSlice"]
            GenSlice["generationSlice"]
            UISlice["uiSlice"]
            TemplatesSlice["templatesSlice"]
            ConfigSlice["configSlice"]
            LogsSlice["logsSlice"]
            ArchSlice["archetypesSlice"]
        end

        subgraph CreatorScreens["Creator Screens"]
            Home["HomeScreen"]
            NewProj["NewProjectWizard"]
            PlanReview["PlanReviewScreen"]
            Board["CollectionBoardScreen"]
            ItemDet["ItemDetailScreen"]
            FuncUpgr["FunctionalUpgradeWizard"]
            Export["ExportScreen"]
            Verify["VerificationScreen"]
        end

        subgraph AdminScreens["Admin Screens"]
            AdminGate["AdminModeGate"]
            AdminTpl["AdminTemplateBrowser"]
            AdminEdit["AdminTemplateEditor"]
            AdminImp["AdminMeshImporter"]
            AdminLog["AdminLogsViewer"]
            AdminJob["AdminJobHistory"]
            AdminRef["AdminReferenceBrowser"]
            AdminCfg["AdminConfigPanel"]
        end

        IPCClient["IPC Client<br/>request / subscribe"]
    end

    Router --> Home
    Router --> NewProj
    Router --> PlanReview
    Router --> Board
    Router --> ItemDet
    Router --> FuncUpgr
    Router --> Export
    Router --> Verify
    Router --> AdminGate
    AdminGate --> AdminTpl
    AdminGate --> AdminEdit
    AdminGate --> AdminImp
    AdminGate --> AdminLog
    AdminGate --> AdminJob
    AdminGate --> AdminRef
    AdminGate --> AdminCfg

    Home -.-> ProjectSlice
    NewProj -.-> ProjectSlice
    PlanReview -.-> ProjectSlice
    PlanReview -.-> GenSlice
    Board -.-> ProjectSlice
    Board -.-> GenSlice
    ItemDet -.-> ProjectSlice
    ItemDet -.-> GenSlice
    FuncUpgr -.-> ArchSlice
    Export -.-> ProjectSlice
    Verify -.-> ProjectSlice
    AdminTpl -.-> TemplatesSlice
    AdminLog -.-> LogsSlice
    AdminCfg -.-> ConfigSlice

    Store -.-> IPCClient
    IPCClient ==> Sidecar["Python Sidecar<br/>(JSON-RPC via stdio)"]

    classDef ui fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000
    classDef store fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000
    classDef admin fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef external fill:#eceff1,stroke:#546e7a,stroke-width:2px,color:#000

    class Home,NewProj,PlanReview,Board,ItemDet,FuncUpgr,Export,Verify,Router ui
    class AdminGate,AdminTpl,AdminEdit,AdminImp,AdminLog,AdminJob,AdminRef,AdminCfg admin
    class ProjectSlice,GenSlice,UISlice,TemplatesSlice,ConfigSlice,LogsSlice,ArchSlice store
    class IPCClient,Sidecar external
```

### 3.4 Deployment Topology

Where files live on the user's machine after installation.

```mermaid
graph TB
    subgraph AppInstall["Application Install Location"]
        AppBundle["App Bundle<br/>Tauri binary + Python sidecar + Tier 1 templates"]
    end

    subgraph AppData["Platform App Data<br/>(macOS: ~/Library/Application Support/AISimsCreator/)<br/>(Windows: %APPDATA%\\AISimsCreator\\)"]
        Tier2Store["tier2_templates/<br/>user-imported"]
        SimsIndex["sims_index.json<br/>resource location cache"]
        ConfigStore["config.json"]
        APIKeys[("System Keyring<br/>API Keys")]
    end

    subgraph DocsLoc["User Documents Location"]
        ProjectsRoot["AISimsCreator/projects/<br/>{project_name}/<br/>  project.sqlite<br/>  assets/<br/>  exports/<br/>  logs/"]
    end

    subgraph PlatLogs["Platform Logs Location"]
        LogFiles["session_*.log"]
    end

    subgraph ExternalInstalls["Pre-existing User Installations"]
        BlenderInst["Blender.app or blender.exe"]
        SimsInst["Sims 4 install directory<br/>(read-only)"]
        ModsDir["Sims 4 Mods folder<br/>(write target)"]
    end

    AppBundle --> Tier2Store
    AppBundle --> ProjectsRoot
    AppBundle --> LogFiles
    AppBundle --> SimsIndex
    AppBundle --> ConfigStore
    AppBundle --> APIKeys
    AppBundle --> BlenderInst
    AppBundle --> SimsInst
    AppBundle --> ModsDir

    classDef app fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef data fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000
    classDef external fill:#eceff1,stroke:#546e7a,stroke-width:2px,color:#000

    class AppBundle app
    class Tier2Store,SimsIndex,ConfigStore,APIKeys,ProjectsRoot,LogFiles data
    class BlenderInst,SimsInst,ModsDir external
```

---

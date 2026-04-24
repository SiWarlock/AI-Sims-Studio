# Diagrams — Cross-Platform and Security Boundaries

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §12, §13

> Cross-platform path resolution per OS, data trust boundaries, file system access permissions.

---

## 12. Cross-Platform Deployment

### 12.1 Path Resolution Per Platform

Side-by-side view of platform-specific paths.

```mermaid
graph TB
    subgraph Mac["macOS"]
        MacApp["App Data:<br/>~/Library/Application Support/AISimsCreator/"]
        MacLogs["Logs:<br/>~/Library/Logs/AISimsCreator/"]
        MacProj["Projects:<br/>~/Documents/AISimsCreator/projects/"]
        MacSims["Sims Install:<br/>/Applications/The Sims 4.app/"]
        MacMods["Mods Folder:<br/>~/Documents/Electronic Arts/The Sims 4/Mods/"]
        MacBlend["Blender:<br/>/Applications/Blender.app/"]
        MacKeychain[("Keychain<br/>API keys")]
    end

    subgraph Win["Windows"]
        WinApp["App Data:<br/>%APPDATA%\\AISimsCreator\\"]
        WinLogs["Logs:<br/>%APPDATA%\\AISimsCreator\\logs\\"]
        WinProj["Projects:<br/>%USERPROFILE%\\Documents\\AISimsCreator\\projects\\"]
        WinSims["Sims Install:<br/>via registry lookup"]
        WinMods["Mods Folder:<br/>%USERPROFILE%\\Documents\\Electronic Arts\\The Sims 4\\Mods\\"]
        WinBlend["Blender:<br/>C:\\Program Files\\Blender Foundation\\"]
        WinCred[("Credential Manager<br/>API keys")]
    end

    subgraph Shared["Shared Abstraction"]
        PathModule["config/paths.py<br/>returns correct paths per OS"]
        KeyringModule["keyring library<br/>platform-agnostic interface"]
    end

    PathModule --> MacApp
    PathModule --> MacLogs
    PathModule --> MacProj
    PathModule --> MacSims
    PathModule --> MacMods
    PathModule --> MacBlend
    PathModule --> WinApp
    PathModule --> WinLogs
    PathModule --> WinProj
    PathModule --> WinSims
    PathModule --> WinMods
    PathModule --> WinBlend

    KeyringModule --> MacKeychain
    KeyringModule --> WinCred

    classDef mac fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000
    classDef win fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef shared fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000

    class MacApp,MacLogs,MacProj,MacSims,MacMods,MacBlend,MacKeychain mac
    class WinApp,WinLogs,WinProj,WinSims,WinMods,WinBlend,WinCred win
    class PathModule,KeyringModule shared
```

---



## 13. Security and Privacy Boundaries

### 13.1 Data Flow Across Trust Boundaries

Which data leaves the user's machine and under what circumstances.

```mermaid
graph TB
    subgraph Local["Fully Local — Never Leaves Machine"]
        UserProjects["User projects<br/>(prompts, edits, metadata)"]
        GeneratedAssets["Generated textures,<br/>thumbnails, packages"]
        Logs["Logs"]
        Config["Configuration"]
        Keys["API Keys<br/>(in platform keyring)"]
    end

    subgraph Sent["Sent to External Services<br/>(minimum necessary)"]
        PromptsToClaude["Prompts + template schemas<br/>→ Anthropic"]
        PromptsToRep["Texture generation prompts<br/>→ Replicate"]
        ResultsFromRep["Generated images<br/>← Replicate"]
    end

    subgraph Never["Never Transmitted"]
        NoTelem["No telemetry"]
        NoAnalytics["No analytics"]
        NoCrash["No crash reports"]
        NoUsage["No usage statistics"]
    end

    UserProjects -.->|prompt portion only| PromptsToClaude
    UserProjects -.->|texture prompts only| PromptsToRep
    ResultsFromRep -.-> GeneratedAssets

    classDef local fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef sent fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000
    classDef never fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000

    class UserProjects,GeneratedAssets,Logs,Config,Keys local
    class PromptsToClaude,PromptsToRep,ResultsFromRep sent
    class NoTelem,NoAnalytics,NoCrash,NoUsage never
```

### 13.2 File System Access Permissions

```mermaid
graph LR
    subgraph ReadWrite["Read + Write"]
        AppData["App Data<br/>config, T2 templates, index cache"]
        ProjectFolder["Project Folders"]
        LogsRW["Logs"]
        ModsFolderW["Mods Folder<br/>(only for own exports)"]
    end

    subgraph ReadOnly["Read-Only"]
        AppBundle["App Bundle<br/>(Tier 1 templates)"]
        SimsInstallRO["Sims 4 Installation"]
        BlenderRO["Blender executable"]
    end

    subgraph Denied["No Access"]
        Other["Any other directory<br/>(user docs, other apps, system)"]
    end

    Sidecar["Python Sidecar"]

    Sidecar ==> ReadWrite
    Sidecar --> ReadOnly
    Sidecar -.->|enforced| Denied

    classDef rw fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef ro fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000
    classDef denied fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef component fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000

    class AppData,ProjectFolder,LogsRW,ModsFolderW rw
    class AppBundle,SimsInstallRO,BlenderRO ro
    class Other denied
    class Sidecar component
```

---

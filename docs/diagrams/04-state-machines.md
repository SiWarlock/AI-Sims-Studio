# Diagrams — State Machines

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §6

> Item, Collection, BuildJob, Swatch, and FunctionalOverlay lifecycles.

---

## 6. State Machines

### 6.1 Item Lifecycle

Every `Item` transitions through a defined set of states.

```mermaid
stateDiagram-v2
    [*] --> Planned: Created from plan
    Planned --> Generating: Generation started
    Generating --> Generated: All stages succeeded
    Generating --> Error: Stage failed after retries
    Generated --> NeedsReview: User flags issue
    Generated --> FunctionalCandidate: User selects for upgrade
    FunctionalCandidate --> Generated: User cancels
    FunctionalCandidate --> Generated: Overlay created (still a generated item, now with overlay)
    Generated --> Excluded: User excludes from export
    Excluded --> Generated: User re-includes
    NeedsReview --> Generating: User regenerates
    Error --> Generating: User retries
    Generated --> ExportReady: Validation passed
    ExportReady --> Exported: Included in successful export
    Exported --> [*]
```

### 6.2 Collection Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft: Project created
    Draft --> Planned: Plan generated
    Planned --> Generating: Generation started
    Generating --> Generated: All items generated
    Generating --> PartialGenerated: Some failures, some successes
    PartialGenerated --> Generating: User retries failed items
    PartialGenerated --> Generated: User accepts partial state
    Generated --> Validating: User opens export
    Validating --> ExportReady: No blockers
    Validating --> BlockedOnIssues: Blockers present
    BlockedOnIssues --> Validating: User resolves issues
    ExportReady --> Exporting: Export triggered
    Exporting --> Exported: Build succeeded
    Exporting --> ExportFailed: Build failed
    ExportFailed --> ExportReady: User retries
    Exported --> Installed: Auto-install succeeded
    Installed --> Verified: User confirms in-game
    Verified --> [*]
```

### 6.3 BuildJob Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Queued: Job created
    Queued --> Running: Scheduler picks up
    Running --> Succeeded: Completed normally
    Running --> Failed: Error after retries
    Running --> Cancelled: User cancels
    Failed --> [*]
    Succeeded --> [*]
    Cancelled --> [*]
```

### 6.4 Swatch Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Planned: Swatch slot allocated
    Planned --> Generating: Texture gen started
    Generating --> Generated: All zones complete
    Generating --> PartialError: Some zones failed
    PartialError --> Generating: User regenerates
    Generated --> Stale: Item spec changed
    Stale --> Generating: Auto-regenerate trigger
    Generated --> [*]
```

### 6.5 Functional Overlay Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Configuring: User in wizard
    Configuring --> Configured: User confirms config
    Configured --> Building: Clone pipeline running
    Building --> Built: Tuning cloned and persisted
    Building --> BuildError: Extraction or clone failed
    BuildError --> Configuring: User retries
    Built --> Stale: Underlying item changed
    Stale --> Building: Re-build triggered
    Built --> [*]: Ready for export
```

---

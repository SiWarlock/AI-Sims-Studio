# Diagrams — Error Flow

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §10

> Error propagation and messaging from failure to creator/admin UI.

---

## 10. Error Flow

### 10.1 Error Propagation and Messaging

How errors move from the point of failure to the user or admin.

```mermaid
graph TB
    Failure["Error occurs<br/>(API, I/O, validation)"]

    Failure --> Classify["Classify<br/>(error taxonomy)"]
    Classify --> Wrap["Wrap in structured error<br/>code + message_user + message_admin"]
    Wrap --> Log["Log via structlog"]
    Wrap --> CheckMode{"Admin mode<br/>active?"}

    CheckMode -->|No| UserMsg["User-facing message<br/>+ suggested action"]
    CheckMode -->|Yes| FullDetail["Full error detail<br/>+ stack trace<br/>+ retry/rebuild context"]

    UserMsg --> CreatorUI["Creator UI displays<br/>friendly error toast"]
    FullDetail --> AdminUI["Admin UI displays<br/>full diagnostic pane"]

    Log --> LogFile[("Session log file")]

    classDef err fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef action fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000
    classDef outcome fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef data fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#000

    class Failure err
    class Classify,Wrap,Log action
    class CheckMode decision
    class UserMsg,FullDetail,CreatorUI,AdminUI outcome
    class LogFile data
```

---

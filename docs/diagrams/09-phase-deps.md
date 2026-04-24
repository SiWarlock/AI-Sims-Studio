# Diagrams — MVP Phase Dependencies

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §11

> Phase sequence and gates, and a representative intra-phase task dependency graph (Phase 3).

---

## 11. MVP Phase Dependencies

### 11.1 Phase Sequence and Gates

How the eight MVP phases depend on each other.

```mermaid
graph TB
    P0["Phase 0<br/>Foundation"]
    P1["Phase 1<br/>Milestone Zero:<br/>Texturing POC"]
    POCGate{"POC<br/>Visual Quality<br/>Gate"}
    Abort["Abort or revise<br/>approach"]
    P2["Phase 2<br/>Template Library"]
    P3["Phase 3<br/>Decorative Pipeline"]
    P4["Phase 4<br/>Validation + Export + Install"]
    P5["Phase 5<br/>Functional Overlay"]
    P6["Phase 6<br/>Admin Mode"]
    P7["Phase 7<br/>Cross-Platform Polish"]
    Release["MVP v1.0<br/>Release"]

    P0 --> P1
    P1 --> POCGate
    POCGate -->|Pass| P2
    POCGate -->|Fail| Abort
    P2 --> P3
    P3 --> P4
    P4 --> P5
    P5 --> P6
    P6 --> P7
    P7 --> Release

    classDef phase fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    classDef gate fill:#fff9c4,stroke:#fbc02d,stroke-width:3px,color:#000
    classDef fail fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    classDef release fill:#e1bee7,stroke:#7b1fa2,stroke-width:3px,color:#000

    class P0,P1,P2,P3,P4,P5,P6,P7 phase
    class POCGate gate
    class Abort fail
    class Release release
```

### 11.2 Task-to-Task Dependencies Within Critical Phase (Phase 3)

Detailed dependency graph for Phase 3 as a representative example of intra-phase structure.

```mermaid
graph TB
    T31["3.1<br/>Anthropic API integration"]
    T32["3.2<br/>Collection planning stage"]
    T33["3.3<br/>Per-item spec gen stage"]
    T34["3.4<br/>Texture gen pipeline"]
    T35["3.5<br/>Thumbnail rendering"]
    T36["3.6<br/>Collection orchestration"]
    T37["3.7<br/>Plan review UI"]
    T38["3.8<br/>Collection board UI"]
    T39["3.9<br/>Item detail UI"]
    T310["3.10<br/>Metadata editing"]
    T311["3.11<br/>Progress event system"]
    T312["3.12<br/>Style parameter plumbing"]

    T31 --> T32
    T31 --> T33
    T32 --> T36
    T33 --> T34
    T33 --> T36
    T34 --> T35
    T34 --> T36
    T35 --> T36
    T32 --> T37
    T36 --> T38
    T36 --> T39
    T36 --> T311
    T39 --> T310
    T33 --> T312
    T34 --> T312

    classDef task fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    class T31,T32,T33,T34,T35,T36,T37,T38,T39,T310,T311,T312 task
```

---

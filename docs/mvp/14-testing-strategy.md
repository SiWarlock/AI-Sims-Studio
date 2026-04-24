# MVP Spec — Testing Strategy

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §11

> Unit, integration, manual acceptance tests, and POC visual quality gate.

---

## 11. Testing Strategy

### 11.1 Unit Tests

Required for all non-UI Python code in the sidecar. Coverage targets:

- Project storage CRUD
- Template schema loading and validation
- Planning stage output parsing and validation
- Item spec generation output validation
- Texture pipeline coordination logic (mockable)
- DBPF read/write operations
- Tuning parsing and targeted editing
- Archetype handlers (with mocked reference resources)
- Validation engine rules
- Path resolution and platform detection

Unit tests must not require network access. AI calls, Replicate calls, and file system operations beyond the test sandbox are mocked.

### 11.2 Integration Tests

Required for the critical paths:

- New project → plan → generation → export → install (decorative only)
- New project → plan → generation → functional upgrade → export → install
- Project rebuild determinism
- Template loader querying across all 19 templates
- Admin mode Tier 2 import and promotion

Integration tests may use a dedicated test Sims install fixture (or documented mocking of the install).

### 11.3 Manual Acceptance Tests

Required for each of the MVP Acceptance Criteria (§10). The final acceptance test run in Task 7.7 executes the full list on both platforms.

Manual acceptance tests specifically require launching Sims 4 and visually confirming items appear and behave correctly. These cannot be fully automated.

### 11.4 POC Visual Quality Gate

Phase 1 concludes with a manual visual quality check by both maintainer and primary user. This is not a pass/fail unit test — it is a subjective quality gate that determines whether the MVP proceeds.

---

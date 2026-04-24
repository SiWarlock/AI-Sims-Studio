# TAD — Validation Engine

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §12

> Structure, check categories, execution, user and admin messaging.

---

## 12. Validation Engine

### 12.1 Structure

The validation engine is a registry of check functions. Each check:

- Declares its target entity type
- Returns zero or more `ValidationIssue`s
- Is pure (depends only on passed-in state, no side effects)

### 12.2 Check Categories

- **Integrity checks** — database consistency, referential integrity, schema conformance
- **Asset checks** — required files exist, are readable, are non-corrupted
- **Content checks** — metadata completeness, valid category assignments, non-empty names
- **Structural checks** — DBPF header valid, TGI IDs non-colliding, required resources present
- **Tuning checks** — cloned tuning valid, references resolvable
- **Archetype checks** — functional overlay archetype compatible with item template

### 12.3 Execution

`validate(collection_id)`:

1. Loads collection and all related entities
2. Runs all applicable checks in parallel where independent
3. Aggregates results into a `ValidationResult`
4. Returns result (does not persist unless explicitly requested)

Validation is fast (target <1 second for a 12-item collection) so it can run on demand.

### 12.4 Messages

Every `ValidationIssue` has both a `message_user` (plain language) and `message_admin` (full detail). The creator UI shows the user messages; admin mode shows both.

---

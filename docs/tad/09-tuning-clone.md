# TAD — Tuning Clone Pipeline

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §11

> Extraction from local Sims install, tuning parsing, clone operation, targeted edits, validation of cloned tuning.

---

## 11. Tuning Clone Pipeline

### 11.1 Extraction

The `sims_install` module reads the user's Sims install lazily:

- On first use, builds an index of `.package` files in the install's Data directory
- Index maps TGI IDs to `(package_path, offset, size)` for fast lookup
- Index is cached under the app data directory
- Index is rebuilt when the Sims install directory's `GameVersion.txt` (or equivalent patch marker) changes

The index is not a full resource extraction; resources are read on demand.

### 11.2 Tuning Parsing

Sims 4 tuning is XML. The `tuning` module:

- Parses tuning XML into a typed tree (using `lxml` for stability and XPath)
- Represents each tunable field as a node with type, value, and references
- Handles special fields: resource references (`TunableReference`), lists, variants
- Preserves unknown fields so clones don't lose data

### 11.3 Clone Operation

To clone a reference object:

1. Read the reference object's tuning resource by ID
2. Parse to typed tree
3. Deep copy the tree
4. Assign new instance IDs to all resource references that must be unique (not shared with the base game)
5. Apply archetype handler's targeted edits (e.g., light color, moodlet reference)
6. Serialize back to XML

### 11.4 Targeted Edit Module

Each archetype handler specifies which fields it can edit. The edit module enforces that only declared fields are modified. This prevents accidental breakage of inherited behavior.

For the MVP archetypes, the editable field lists are documented in each handler module.

### 11.5 Validation of Cloned Tuning

After cloning, tuning is validated:

- All resource references are resolvable (either to new resources the app is creating, or to base-game resources that exist in the user's install)
- No syntactically invalid XML
- No fields with out-of-range values per the archetype handler's configuration schema

Validation failures here are blocking errors.

---

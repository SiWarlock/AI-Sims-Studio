---
description: Look up a specific functional requirement (FR-###) from the PRD without loading the full PRD.
argument-hint: [FR-id e.g. FR-025 or just 025]
allowed-tools: Read, Grep
---

Look up functional requirement `$ARGUMENTS`.

Steps:

1. Normalize the ID. Accept `FR-025`, `fr-025`, `FR-25`, or bare `025` / `25`. Convert to the form `FR-###` with leading zeros (`FR-025`).
2. Load `docs/prd/07-functional-requirements.md`.
3. Find the FR by ID.
4. Report:
   - The FR's exact wording
   - The feature area it belongs to (e.g., "Project Management", "Generation", "Functional Overlay")
   - Related FRs if any are referenced in its body
   - Any ACs (acceptance criteria) that directly verify this FR (cross-reference with `docs/prd/09-acceptance-and-guardrails.md` and `docs/mvp/13-acceptance-criteria.md` if the FR is MVP-scoped)

If the FR doesn't exist, report that and list the nearest valid IDs.

Do not load other docs unless specifically needed for cross-reference.

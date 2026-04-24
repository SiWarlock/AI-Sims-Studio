---
description: Look up a specific acceptance criterion (AC-### or MVP-AC-###) from the appropriate source document.
argument-hint: [AC-id e.g. AC-007 or MVP-AC-012]
allowed-tools: Read, Grep
---

Look up acceptance criterion `$ARGUMENTS`.

Steps:

1. **Determine the source document from the ID prefix:**
   - `MVP-AC-###` → `docs/mvp/13-acceptance-criteria.md`
   - `AC-###` (no MVP prefix) → `docs/prd/09-acceptance-and-guardrails.md`
   - If the prefix is ambiguous or missing, ask which the user means before loading.
2. **Normalize the numeric portion** to zero-padded 3 digits (`AC-7` → `AC-007`).
3. **Load only the one source document** needed — never both.
4. **Find and report:**
   - The AC's exact wording
   - What it's verifying (behavior, output, constraint)
   - Which FRs this AC verifies (if cross-referenced)
   - What code would need to exist to satisfy it

If the AC doesn't exist, report that and list the nearest valid IDs.

To actually verify the code against the AC (not just look up its wording), use `/check-acceptance` instead.

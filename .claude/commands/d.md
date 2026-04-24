---
description: Look up a deferred decision (D-1 through D-6) and its current resolution status from the MVP Spec.
argument-hint: [D-id e.g. D-1 or just 1]
allowed-tools: Read, Grep
---

Look up deferred decision `$ARGUMENTS`.

Steps:

1. Normalize the ID. Accept `D-1`, `d-1`, `D1`, or bare `1`. Convert to `D-#`.
2. Load `docs/mvp/04-deferred-decisions.md`.
3. Find the decision and report:
   - The decision question
   - The option space (candidates under consideration)
   - The resolution timeline (typically Phase 1 POC)
   - The current status — look for any resolution text. If resolved, report the chosen option and any implementation notes.
4. Cross-check `docs/mvp/15-supporting.md` (decisions log) for any resolution recorded there.
5. If resolved: confirm the resolution is reflected in the codebase by grepping for the relevant modules.

Valid IDs: D-1, D-2, D-3, D-4, D-5, D-6.

- **D-1:** DBPF library (sims4-tools vs custom)
- **D-2:** Image model on Replicate
- **D-3:** Normal/specular map derivation
- **D-4:** Exact base-game reference object TGI IDs
- **D-5:** Blender render recipe details
- **D-6:** Texture resolution (1K vs 2K default)

If the ID isn't in this list, report that it's not a known deferred decision.

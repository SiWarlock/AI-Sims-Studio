# MVP Spec — Phase 7 — Cross-Platform Hardening and Polish

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.8

> Windows parity, path edge cases, Blender discovery polish, documentation deliverables.

---

**Phase goal:** Final cross-platform testing, edge case handling, polish, documentation, and release readiness.

**Phase acceptance gate:** Both macOS and Windows builds pass all acceptance criteria in §10. Documentation deliverables in §13 are complete.

#### Tasks

**7.1 — Cross-platform parity testing**
Run the full MVP acceptance test suite on both Mac and Windows. Fix any platform-specific divergences.

*Outputs:* All ACs pass on both platforms. Divergences documented and fixed.
*Dependencies:* All prior phases.
*Acceptance:* Identical projects produce identical exports on both platforms.

**7.2 — Path edge case handling**
Handle non-standard Sims install locations, Mods folder on different drives, and permission edge cases. Provide manual overrides where auto-detection fails.

*Outputs:* Robust path handling across edge cases.
*Dependencies:* 0.3, 0.4, 4.4.
*Acceptance:* Non-standard installs work via manual override. Permission errors produce clear messages.

**7.3 — Error message polish**
Review every user-facing error message for clarity, actionability, and tone. Replace jargon with plain language. Ensure every error surfaces a next step.

*Outputs:* Polished error message set across the entire app.
*Dependencies:* All prior phases.
*Acceptance:* Primary user can understand and act on every error.

**7.4 — README**
Write the repository README covering project overview, dev setup, build instructions for both platforms, and contributing notes.

*Outputs:* `README.md` in the repo root.
*Dependencies:* All prior phases.
*Acceptance:* A developer cloning the repo can follow the README and get a working dev environment.

**7.5 — User manual**
Write a user-facing guide for the primary creator (girlfriend). Cover installation, first-project walkthrough, collection creation, functional upgrades, export and install, verification. Use plain language. Include screenshots.

*Outputs:* User manual in the repo, packaged with the app.
*Dependencies:* All prior phases.
*Acceptance:* A non-technical reader can follow the guide and complete a collection end-to-end.

**7.6 — Maintainer guide**
Write a maintainer-facing guide covering admin mode, template authoring, debugging workflows, Windows tooling recommendations (S4Studio, Sims4Tools, Mod Constructor, XML Extractor), common failure modes and recovery.

*Outputs:* Maintainer guide in the repo.
*Dependencies:* All prior phases.
*Acceptance:* The maintainer can reference the guide to perform any supported admin task.

**7.7 — Final acceptance test run**
Execute the full acceptance criteria list from the PRD (AC-001 through AC-016) and from §10 of this document. Sign off MVP completion.

*Outputs:* Completed acceptance test log.
*Dependencies:* All prior tasks.
*Acceptance:* All ACs pass. MVP v1.0 is shipped.

---

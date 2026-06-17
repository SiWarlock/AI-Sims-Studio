# Anchor Remap — draft `#sec-N` → binding `§N`

> The draft (`docs/planning/ARCHITECTURE_DRAFT.md`) used `#sec-1…#sec-23`. The binding `ARCHITECTURE.md`
> conforms to the repo template (`§1/§2/§2.5/§3…§22` + Spec Anchor Index + Appendix A). Downstream binds to
> the **binding `§` anchors**. `DECISIONS.md` "Anchors:" lines and `DIAGRAM_PLAN.md` "Spec anchors:" entries
> resolve through this table (DIAGRAM_PLAN updated in-place to final `§`).

| Draft anchor | Binding anchor(s) | Notes |
|---|---|---|
| `#sec-1` Exec summary | Executive summary | — |
| `#sec-1a` Goals/Non-goals | §1 | — |
| `#sec-2` Scope | §1, §20 | scope/guardrails moved to §20 |
| `#sec-3` Locked decisions | Exec summary table + `DECISIONS.md` | — |
| `#sec-4` System overview | §2 | — |
| `#sec-4a` Dependency DAG/seams | §2.5 | cross-edges corrected (C↔D GEOM seam, F→D, B→C/D) |
| `#sec-5` Domain model | §12 | + new states (skipped/unsupported/cancelled/AssetVariant/…) |
| `#sec-6` Core modules/contracts | §4, §5, §6, §7, §8, §9, §10, §11 | split into per-subsystem sections |
| `#sec-7` Data/state | §12, §13 | source-of-truth = Postgres authoritative |
| `#sec-8` User flows | §2 + `USER_FLOWS.md` | — |
| `#sec-9` Integrations | §7, §8, §9, §14 | — |
| `#sec-10` Automation | §5, §6, §17 | — |
| `#sec-11` Frontend | §3 | + onboarding/Settings = §18 |
| `#sec-12` Backend/pipeline | §5, §6 | — |
| `#sec-13` Shared/config | §4, §11, §21 | — |
| `#sec-14` Testing/evals | §15 | EVAL-004/006/007/008 reframed |
| `#sec-15` Security/risk | §16 + `RISKS.md` | — |
| `#sec-16` Deployment | §19 | + notarization/rollback/migration |
| `#sec-17` Alternatives | `DECISIONS.md` | — |
| `#sec-18` Scope/deferred | §20 | — |
| `#sec-19` Diagrams | `DIAGRAM_PLAN.md` | — |
| `#sec-20` Repo scaffold | (carried in `ARCHITECTURE_DRAFT §20`) | tasks-gen may consume; not duplicated in binding doc |
| `#sec-21` Decision summary | Exec table + `DECISIONS.md` | — |
| `#sec-22` Spec anchor index | Spec Anchor Index | — |
| `#sec-23` Review instructions | `CLAUDE_CODE_HANDOFF.md` | — |
| *(new)* | §10 Donor Library | audit-added subsystem |
| *(new)* | §17 Error taxonomy | audit-added (`ErrorEnvelope`) |
| *(new)* | §18 Onboarding/Settings | audit-added subsystem |

# Team Handoff providers-001 — Phase 3 providers, round 1 pause

**Date:** 2026-06-18
**Track:** providers (Phase 3 — real provider adapters behind frozen §7 interfaces + bakeoffs + §16 validation)
**Worktree:** `../AISimsStudio-providers` (branch `track/providers`) — left in place (track pausing, not done)
**Predecessor handoff:** first handoff (this track forked off `track/contract` after Phase 0 sealed)
**Successor handoff:** _(filled in when the next /team-end runs)_
**Round-seal commit at handoff:** `9aaa9cb`

## Why this handoff exists
Auto-cycle: implementer hit the ACTION context tier (79%) at a clean slice boundary (fal landed, no slice in flight) + the user's "seal after fal" decision — round sealed and team paused. The track's critical remainder (3.1) is blocked on the spikes-S2 verdict, so there is no unblocked high-priority work to continue into.

## Team composition at close
- **Lead:** this session (track `providers`, session `2d480d36`)
- **Orchestrator:** `providers-adapters-orchestrator` — session `03f0948f` — last commit `9aaa9cb` (/orchestrate-end round seal)
- **Implementer:** `providers-adapters-implementer` (area `services/pipeline/adapters`) — session `2c346315` — session doc `d248819`; last feature commit `6ed415b`
- All teammates `/session-end` + `/orchestrate-end` closed at round-seal `9aaa9cb`; both processes spun down via `shutdown_request`.

## Active arc + where it landed
Arc: real, model-agnostic Phase-3 provider adapters behind the frozen §7 Protocols. **Round 1 delivered** the full adapter foundation (`_http` secret-free transport · `errors` §17 HTTP→ErrorCode classifier · `validation` §16 SSRF + streaming byte-cap · `pricing` cost table) plus **3.3 LLM** (Claude + OpenRouter), **3.4 §16 provider-output validation** (3.4a magic-byte/candidate-cap/SSRF + 3.4b cost capture), and **3.2 concept-image** with **two** imagegen backends (WaveSpeed FLUX.2 default + silhouette gate + pinned seed, and fal-FLUX alternate) → **EVAL-002 bakeoff unblocked**. Reviews caught + fixed 3 "poll-never-raises" bugs and a HIGH SSRF bug, all in-slice. Suite green throughout; `mypy --strict` clean.
Next planned slice: **3.1 image-to-3D** (fal + WaveSpeed) — the critical remainder, **BLOCKED on spikes-S2** (S2's verdict refines the image-to-3D defaults).

## In-flight at close
None — clean close. Working tree clean; no slice in flight.

## Carry-forward to next team session
- **3.1 image-to-3D — BLOCKED on spikes-S2** (cross-track). The critical remainder; resumes once S2 lands. Pulls in mesh ContentKinds + image3d wiring.
- **Deferred breadth (lead+user-approved deferrals):** rembg own-slice (heavy onnxruntime + ~170MB model; carries a bundle-vs-first-run-fetch packaging decision) · Replicate concept-image backend · OpenRouter image-gen (research-required/research-gated).
- **Phase-2 hardening carry-forwards:** SSRF resolve→connect TOCTOU → Phase-2 transport IP-pinning · LLM node-level cost + run-rollup (REQ-NF-103) → Phase-2 · WaveSpeed billing reconcile + price-table tuning → Phase-2/3.4b · fal cassette live re-record (metrics location / result-URL / png alpha) before fal production-trust.
- Full detail in the session doc: `docs/sessions/providers-001-2026-06-18-phase-3-provider-adapters.md` "Open follow-ups".

## Open decisions / blockers for the human
1. **3.1 resume is gated on the spikes-S2 verdict** (cross-track dependency). Coordinate with the spikes track before resuming the providers track on 3.1.
2. **Integration merge of `track/providers` → integration/main is pending** (you coordinate merges). At the merge, apply the orchestrator's staged **shared-root edits** (NOT committed on `track/providers` to avoid conflict):
   - **PLAN ticks:** 3.3 `[x]` (LLM Claude+OpenRouter) · 3.4 `[x]` (3.4a §16 + 3.4b cost) · 3.2 landed-scope (WaveSpeed default + silhouette gate + pinned seed + fal alternate; Replicate/OpenRouter/rembg are approved continuation) · 3.1 `[ ]` (S2-blocked) · **+ a "team paused 2026-06-18 — handoff providers-001 — round-seal `9aaa9cb`" marker under Currently in progress.**
   - **PLAN Log entry** (2026-06-18 providers round) + the carry-forwards above.
   - **ARCH notes:** §7 (real LLM/ImageGen backends behind factory seams; ProviderError in neutral `errors.py`; `pricing.py` cost) · §16 (`validation.py` + SSRF/streaming-cap `get_bytes`; error-code split; fail-closed not-is-global floor).
3. **Prioritization call:** whether to do the deferred breadth (Replicate / OpenRouter / rembg) in a next round, or hold the providers track entirely until S2 unblocks 3.1.
4. **Finding 2 (tooling, scaffolding-template):** the whole-pipeline `mypy` pre-commit hook runs over untracked files, fighting bisectable commit splits when a later-commit test references not-yet-applied prod changes. Worked around cleanly in-round (no `--no-verify`); worth a template fix.

## Spawn prompts ready for the next team session

**Orchestrator:**
```
You are providers-adapters-orchestrator on the AI Sims Creator agent team.
Track: providers. Team label: providers. Worktree: /Users/dreddy/Documents/Dev/AISimsStudio-providers (branch track/providers) — cd there first; commits land on track/providers, never root. Route shared-root-doc edits to the integration checkout at /Users/dreddy/Documents/Dev/AISimsStudio.
Ignore peer DMs without the `providers-` prefix (channel-bleed).
Activated because: resuming Phase 3 providers, round 2. Round 1 (foundation + 3.3 + 3.4 + 3.2/2-backends) sealed at 9aaa9cb. <If S2 has landed: dispatch 3.1 image-to-3D, folding S2's verdict into the defaults.> <Else: pick up the approved deferred breadth — Replicate / OpenRouter(research-gated) / rembg — per the user's prioritization.>
FIRST ACTIONS: (1) cd /Users/dreddy/Documents/Dev/AISimsStudio-providers (2) ~/.claude/scripts/team-register.sh "providers-adapters-orchestrator" orchestrator "providers" "" "providers" "track/providers" (3) /orchestrate-start (NOT /session-start).
Confirm: start command ran, registry entry written (echo $CLAUDE_CODE_SESSION_ID distinct from lead), first slice proposed.
```

**Implementer (`adapters` / `services/pipeline`):**
```
You are providers-adapters-implementer on the AI Sims Creator agent team.
Track: providers. Team label: providers. Working directory: /Users/dreddy/Documents/Dev/AISimsStudio-providers/services/pipeline/ — cd there first; commits land on track/providers, never root. Talk only to providers-adapters-orchestrator; ignore other prefixes.
Activated because: resuming Phase 3 providers round 2 — orchestrator is authoring the next brief (3.1 image-to-3D if S2 landed, else deferred breadth). Orient and await dispatch.
FIRST ACTIONS: (1) cd /Users/dreddy/Documents/Dev/AISimsStudio-providers/services/pipeline (2) ~/.claude/scripts/team-register.sh "providers-adapters-implementer" implementer "providers" "adapters" "providers" "track/providers" (3) /session-start (NOT /orchestrate-start).
Confirm: start command ran, registry entry written + distinct session id.
```

## How to resume
Next team session: lead runs `/team-start providers`, reads this handoff doc + `IMPLEMENTATION_PLAN.md` "Currently in progress" on demand, spawns teammates using the prompts above (fill the S2-landed vs not branch in the orchestrator's "activated because"), verifies read-backs. **Confirm the spikes-S2 verdict status first** — it gates whether 3.1 is dispatchable or the round does deferred breadth only.

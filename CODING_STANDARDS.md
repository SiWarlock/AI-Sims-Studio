# AI Sims Creator — Coding Standards

This document defines the non-negotiable coding rules for the project. Violations block merges via pre-commit and pre-push hooks.

This is a reference. You do not need to memorize it — tooling enforces most of it. But read through the "rules you must internalize" section once, because some rules are architectural, not stylistic.

## Rules You Must Internalize

These are rules tooling cannot fully enforce. Violating them is a merge-blocker in code review.

1. **Schema-first data flow.** All data crossing module boundaries — especially the IPC boundary, storage boundary, and pipeline-stage boundaries — passes through Pydantic v2 models. No dicts, no dataclasses, no `Any`. The frontend receives TypeScript types generated from these schemas.
2. **Pure stage functions.** Every pipeline stage is an async function that takes a typed input and returns a typed output. No side effects beyond its declared responsibilities. External clients (Anthropic, Replicate, Blender) are injected as dependencies so tests can mock them.
3. **Structured errors, never bare exceptions.** Every user-facing failure raises a subclass of `AISCError` with an `error_code`, `message_user`, `message_admin`, and `retriable` flag. See `docs/tad/14-errors-logging.md`.
4. **Logs via `structlog`, never `print`.** Every log has a structured event name and typed context fields.
5. **AI never produces game-compatible outputs directly.** AI contributes to planning, prompts, metadata drafting, and tuning *values*. Deterministic code handles DBPF packaging, DDS encoding, tuning XML assembly, and mesh loading.
6. **One responsibility per module.** If a file grows past ~400 lines, split it.
7. **Cross-platform parity.** If you add platform-specific code, it lives in `sidecar/aisc/config/paths.py` or an equivalently isolated module. Never scatter `if sys.platform == ...` throughout the codebase.
8. **No hidden state.** State lives in SQLite or the file tree under the project folder. No globals, no module-level caches of user data.

## Python Rules (sidecar)

### Style and formatting

- **Formatter:** `ruff format` (configured in `pyproject.toml`).
- **Linter:** `ruff check` with the rule set pinned in `pyproject.toml`.
- **Type checker:** `mypy --strict`. Zero errors allowed.
- **Line length:** 100 characters. `ruff format` handles wrapping.
- **Indentation:** 4 spaces. No tabs.
- **Imports:** ordered as stdlib → third-party → first-party, separated by blank lines. `ruff` enforces this.

### Typing

- **Type hints required** on every function signature. Return types included even when obvious.
- **`Any` is forbidden** except at external-library adapter boundaries, where it must be wrapped and typed within 3 lines.
- **Use `TypeAlias` or `NewType`** for domain-specific primitive types (e.g. `TemplateId = NewType("TemplateId", str)`).
- **Prefer `|` over `Optional` and `Union`** in Python 3.10+ style (`str | None`, not `Optional[str]`).
- **No implicit generics.** Write `list[int]` not `list` when a type is parameterized.

### Async

- **`asyncio` is the default.** Sync code is a code smell unless the operation is demonstrably CPU-bound or blocking-IO wrapped in `run_in_executor`.
- **No `threading.Thread` for pipeline work.** Use `asyncio.create_task` or `asyncio.TaskGroup`.
- **Blender subprocess, DBPF writes, and large image encoding run in the thread pool executor** via `loop.run_in_executor` to avoid blocking the event loop.
- **Never call `asyncio.run()` inside library code.** Only at the sidecar entry point.

### Pydantic

- **All data models are Pydantic v2.** Use `BaseModel`, `Field`, `field_validator`, `model_validator`.
- **Every model declares `model_config = ConfigDict(frozen=True, extra="forbid")`** unless there's a documented reason not to.
- **Field names in snake_case.** JSON serialization is automatic via Pydantic.
- **Every schema version field starts at 1.** Bump when a breaking change lands, with a migration.

### Errors

- **Every error raises a subclass of `AISCError`.** See `sidecar/aisc/errors/`.
- **`AISCError` subclasses declare their `error_code` at class level** as a class variable. This enum is mirrored in `shared-types/`.
- **Never raise plain `Exception`, `ValueError`, `RuntimeError`** outside of `AISCError.__init__`. Wrap third-party exceptions at module boundaries.
- **Every error has a `message_user` (plain language) and a `message_admin` (full detail with stack context).** The IPC layer renders these into JSON-RPC error responses.

### Logging

- **`structlog` only.** No `print`, no stdlib `logging` directly.
- **Every log entry has an event name** as the first positional arg: `logger.info("texture_generated", item_id=item.id, swatch_index=i, duration_ms=elapsed)`.
- **No sensitive data in logs.** API keys, full prompts, and raw user data are redacted at the logger level. Admin-mode verbose logging can unredact.

### Module boundaries

- **Inside `sidecar/aisc/`, modules declare their public API in `__init__.py`.**
- **No cross-module imports that skip the package boundary.** `from sidecar.aisc.storage.internal_helpers import ...` is forbidden; use what `storage/__init__.py` exports.
- **Circular imports are a design bug.** If you hit one, refactor the dependency, do not use lazy imports.

### Tests (Python)

- **pytest, pytest-asyncio, pytest-mock.** No unittest.
- **Every new non-trivial module gets unit tests in the same PR.**
- **Every new IPC handler gets a happy-path + one failure-path integration test.**
- **External dependencies are mocked.** No network calls in unit tests. No Blender calls. No Sims install reads.
- **Use fixtures in `tests/fixtures/` for reusable test data.**
- **Coverage target: 80%+ on non-UI code.** Coverage is measured by `pytest --cov`.
- **Test file naming:** `test_{module_name}.py` in a parallel `tests/` tree.

## TypeScript Rules (frontend)

### Style and formatting

- **Formatter:** `prettier` (config in `frontend/`).
- **Linter:** `eslint` with the rule set pinned in `frontend/.eslintrc.cjs`.
- **Type checker:** `tsc --noEmit`. Strict mode. Zero errors allowed.
- **Line length:** 100 characters.
- **Indentation:** 2 spaces.

### Typing

- **`strict: true` in `tsconfig.json`.** Non-negotiable.
- **`any` is forbidden** except at external-library adapter boundaries with an `eslint-disable-next-line` comment explaining why.
- **IPC payload types come from `shared-types/`.** Never hand-write a type that crosses the IPC boundary.
- **Component props have explicit interfaces.** Inline object types are acceptable only for internal/helper types.
- **Redux state slices have explicit interfaces** for their state shape.

### React

- **Function components only.** No class components.
- **Hooks at the top of the component body**, before any JSX.
- **No component exceeds ~300 lines.** Split into sub-components.
- **No inline prop objects or arrow functions on high-frequency render paths.** Memoize with `useMemo` / `useCallback` where profiling indicates.
- **Single default export per file.** Named exports for helpers are fine.

### Redux Toolkit

- **One slice per feature in `frontend/src/store/slices/`.**
- **No cross-slice imports.** If two slices need to coordinate, use middleware or colocate them into a larger slice.
- **Async work uses `createAsyncThunk`.**
- **Never mutate state outside a reducer.** RTK's Immer-backed reducers handle the apparent mutation.
- **Selectors live next to their slice** and are typed.

### Styling

- **Tailwind CSS for most styling.** Class-based utility approach.
- **CSS modules only for component-scoped quirks** that Tailwind can't express cleanly.
- **No inline styles** except for dynamic values that can't be expressed as classes.
- **No global CSS additions** outside of the root Tailwind setup.

### Tests (TypeScript)

- **vitest + React Testing Library.**
- **Test component behavior, not implementation details.** Query by role/label, not by class name or test ID except as a last resort.
- **Mock IPC calls via a test harness** that swaps the `IPCClient` for a canned implementation.
- **No `waitFor` with long timeouts.** If a test needs long waits, the design is wrong.

## Testing Rules (both stacks)

- **Unit tests** are required for all non-UI logic.
- **Integration tests** are required for critical paths (listed in `docs/mvp/14-testing-strategy.md`).
- **Manual acceptance tests** are executed during Phase 7 against every MVP-AC-###.
- **Tests run on pre-push hook.** Don't push if they fail locally.
- **Determinism tests:** for DBPF packaging, thumbnail rendering, and TGI generation, tests verify byte-identical output on rebuild.
- **Platform parity:** integration tests tagged `@platform_parity` run on both macOS and Windows and verify identical outputs.

## Commit Rules

### Conventional Commits

Format: `type(scope): description (optional-ref)`

- **`type`:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `build`, `ci`, `perf`, `style`.
- **`scope`:** the module or feature area. Examples: `storage`, `ipc`, `texture_gen`, `frontend/collection-board`, `archetypes/light`.
- **`description`:** imperative present tense, lowercase start. No period at end.
- **`ref`:** reference an FR or AC where relevant: `feat(storage): add project CRUD (FR-001, FR-002)`.

### Commit discipline

- **One logical change per commit.** Split unrelated changes into separate commits even within one PR.
- **Commits compile.** Every commit should leave the repo in a working state. Use `git rebase -i` to clean up history before pushing.
- **No WIP commits in the final history.** Squash-merge handles this at the PR level, but prefer clean local history anyway.
- **Commit messages reference the shard, not the monolith** when citing docs: `refactor(pipelines): simplify planning stage per docs/tad/04-pipelines.md §6.1`.

### Commit size

- A typical commit is 50-300 lines of diff.
- If a commit is over 500 lines, consider splitting.
- Exception: initial scaffolding commits (Phase 0) and generated files (shared types, migrations) may be larger.

## Pull Request Rules

### Branch naming

`phase-{N}/task-{X.Y}-short-slug`

Examples:

- `phase-0/task-0.5-project-storage-layer`
- `phase-3/task-3.4-texture-generation-pipeline`
- `phase-5/task-5.4-light-archetype-handler`

### PR target

- Feature branches → `dev` always.
- Never push directly to `main` or `dev`.
- `main` promotions happen at phase-complete milestones via a separate promotion PR.

### PR title

`[Phase {N}] Task {X.Y}: Short description`

Example: `[Phase 0] Task 0.5: Project storage layer`

### PR description

A PR description must include:

1. **What task this implements** (task number + one-sentence description).
2. **Which FRs and ACs this satisfies** (if any).
3. **What's in scope / out of scope** (note anything discovered but deferred to a follow-up).
4. **Testing notes** (what was tested, what couldn't be, any manual steps).
5. **Screenshots** (for any UI changes).

### Pre-PR checks

Before opening a PR, run `/review-pr`. It will:

1. Lint Python and TypeScript.
2. Type check both.
3. Run unit tests for changed modules.
4. Verify `shared-types/` is in sync with Pydantic schemas.
5. Check for accidental direct `main`/`dev` commits in branch history.

These checks are enforced by the pre-push hook, but running `/review-pr` before opening makes PR review faster.

### Merge strategy

Squash-merge into `dev` with a cleaned-up message. The PR title becomes the squash-commit message.

## Hook Behavior (strict mode)

All hooks are strict — they block the operation if checks fail. No advisory warnings.

- **Pre-commit:** `ruff`, `mypy`, `eslint`, `tsc --noEmit`, codegen sync check, relevant unit tests for changed modules.
- **Pre-push:** full Python unit suite, integration tests on critical paths.
- **Post-edit (Pydantic):** auto-regenerate TypeScript types and stage them.

If a hook blocks you and you think the block is wrong, fix the hook (in a separate PR) rather than bypassing it. `--no-verify` is never used on this project.

## What Belongs Where

Quick reference for where to add new things:

| Adding... | Goes in... |
|---|---|
| New Pydantic schema | `sidecar/aisc/schemas/{domain}.py` |
| New IPC handler | `sidecar/aisc/ipc/handlers/{namespace}.py` |
| New pipeline stage | `sidecar/aisc/{stage_name}/` (new package) |
| New archetype | `sidecar/aisc/archetypes/{archetype_name}.py` |
| New Redux slice | `frontend/src/store/slices/{slice_name}.ts` |
| New screen | `frontend/src/screens/{ScreenName}.tsx` |
| New reusable component | `frontend/src/components/{Name}/` |
| New template (Tier 1) | `templates/{decor|furniture}/{template_id}/` |
| New Blender script | `scripts/blender/{purpose}.py` |
| New slash command | `.claude/commands/{command-name}.md` |
| New doc shard | `docs/{area}/{XX-slug}.md` + update `docs/README.md` and `docs/CLAUDE.md` |

## Tooling Configs (authoritative sources)

- **Python formatter/linter:** `pyproject.toml` under `[tool.ruff]`
- **Python type checker:** `pyproject.toml` under `[tool.mypy]`
- **Python tests:** `pyproject.toml` under `[tool.pytest.ini_options]`
- **TypeScript type checker:** `frontend/tsconfig.json`
- **TypeScript linter:** `frontend/.eslintrc.cjs`
- **TypeScript formatter:** `frontend/.prettierrc`
- **Tauri config:** `frontend/src-tauri/tauri.conf.json`

If you want to change a rule here, change the tooling config and update this document in the same PR. These two must stay in sync.

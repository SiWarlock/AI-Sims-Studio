---
description: Run tests by class. cwd-aware. Usage: /run-tests [unit|integration|all]
allowed-tools: Bash
argument-hint: "[unit|integration|all]"
---

Run tests by class. **cwd-aware** — runs the right test runner for whichever code area you're in.

Argument: `$ARGUMENTS` — see the mapping table(s) below. Default: `unit`.

## Step 0 — Detect mode

```bash
case "$(pwd)" in
  */desktop|*/desktop/*)     MODE=the\ desktop\ UI ;;
  */pipeline|*/pipeline/*)   MODE=the\ Python\ pipeline\ sidecar ;;
  */export|*/export/*)       MODE=the\ Sims\ DBPF\ export\ worker ;;
  */blender|*/blender/*)     MODE=the\ Blender\ mesh/GEOM\ worker\ \(bpy\) ;;
  */contracts|*/contracts/*) MODE=the\ shared\ contracts\ package\ \(pydantic→TS\ codegen\) ;;
  */evals|*/evals/*)         MODE=the\ eval\ harnesses\ \(LangSmith-native\ +\ metric\ layer\) ;;
  *)                         MODE=unknown ;;
esac
```

Announce the detected mode before running. If `MODE=unknown` (repo root or unrecognized directory), surface the cwd and ask which area before running.

---

## the desktop UI mode mapping

| Argument | Command |
|---|---|
| (empty / `unit`) | `pnpm test:run` |
| `integration` | `pnpm test:run` (integration suite) |
| `all` | `pnpm test:run` |
| `<path>` | `pnpm test:run <path>` |

## the Python pipeline sidecar mode mapping

| Argument | Command |
|---|---|
| (empty / `unit`) | `uv run pytest -m unit` |
| `integration` | `uv run pytest -m integration` |
| `all` | `uv run pytest` |
| `<path>` | `uv run pytest <path> -v` |

## the Sims DBPF export worker mode mapping

| Argument | Command |
|---|---|
| (empty / `unit`) | `pnpm test:run` |
| `integration` | `pnpm test:run` (integration suite) |
| `all` | `pnpm test:run` |
| `<path>` | `pnpm test:run <path>` |

## the Blender mesh/GEOM worker (bpy) mode mapping

| Argument | Command |
|---|---|
| (empty / `unit`) | `uv run pytest -m unit` |
| `integration` | `blender --background` integration suite (`uv run pytest -m integration`) |
| `all` | `uv run pytest` |
| `<path>` | `uv run pytest <path> -v` |

## the shared contracts package (pydantic→TS codegen) mode mapping

| Argument | Command |
|---|---|
| (empty / `unit`) | `uv run pytest -m unit` |
| `snapshot` | `uv run pytest -m snapshot` |
| `all` | `uv run pytest` |
| `<path>` | `uv run pytest <path> -v` |

## the eval harnesses (LangSmith-native + metric layer) mode mapping

| Argument | Command |
|---|---|
| (empty / `unit`) | `uv run pytest -m unit` |
| `eval` | `uv run pytest -m langsmith` |
| `all` | `uv run pytest` |
| `<path>` | `uv run pytest <path> -v` |

If an argument names a class that belongs to a *different* mode, **ERROR** with a clear message naming the expected cwd.

---

<!-- ▼ EXAMPLE BLOCK [id=test-class-discipline-notes]: test-class discipline notes — OPTIONAL. Some test classes
     need preconditions (a live external dependency, an env var, a slow browser).
     The source project documented things like: "the live-attack class needs a
     reachable target + a bearer env var, else it skips with a clear message;"
     "the visual-smoke class is slow — run per-PR, not per-commit." Add the
     project's own per-class discipline notes here, or delete this block. ▼ -->
<!-- ▲ END EXAMPLE BLOCK [id=test-class-discipline-notes] ▲ -->

## Output

Report:
- Mode (which code area)
- Test count + class
- Pass / fail counts
- First ~20 lines of any failure
- Total duration

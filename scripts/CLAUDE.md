# Scripts — Claude Code Guidance

You are working inside `/scripts/`. This directory contains standalone Python scripts for:

- Code generation (Pydantic → TypeScript)
- Blender subprocess invocations
- Build automation
- Development tooling (template validation, preview rendering, etc.)

Scripts are executable entry points, not library code. They're invoked from command line, CI, or subprocess calls, not imported by the app.

## Layout

```
scripts/
├── generate_types.py                # Pydantic schemas → shared-types/index.ts
├── validate_template.py             # check a template's manifest + mesh integrity
├── render_template_previews.py      # maintainer-facing thumbnails for admin browser
├── shard_docs.py                    # (lives at repo root, not here)
├── build.sh                         # macOS build entry point
├── build.ps1                        # Windows build entry point
└── blender/                         # Blender Python scripts (invoked via subprocess)
    ├── render_thumbnail.py          # item thumbnail rendering (called from sidecar)
    ├── render_template_preview.py   # maintainer template previews
    └── template_starter.blend       # (optional) blank template starting point
```

## Hard Rules

1. **Every script has a `__main__` guard and an `argparse` interface.** No positional arg guessing.
2. **Every script has a docstring at the top** explaining what it does, when to run it, and what it outputs.
3. **Scripts exit with non-zero on failure.** No silent failures. Exceptions are either caught and re-raised with a clear message, or printed and `sys.exit(1)`.
4. **Scripts are idempotent where possible.** Running twice produces the same result. Running after a failed partial run recovers cleanly.
5. **Scripts can be run independently.** No cross-script assumptions about state. Each script fully resolves its own inputs/outputs.
6. **Scripts that invoke the sidecar package use the sidecar's virtual environment.** Don't reinvent helpers — import from `aisc.*` instead.
7. **Blender scripts live in `scripts/blender/` and are run via `blender --python`.** They have access to `bpy` only when invoked inside Blender.

## Script Template

Use this as a starting point when adding a new script:

```python
#!/usr/bin/env python
"""
Short description of what this script does.

Usage:
    python scripts/foo.py --input <path> --output <path>

Run this script:
    - During CI after Pydantic schema changes (for generate_types.py)
    - Manually to refresh template previews (for render_template_previews.py)
    - etc.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        do_the_work(args.input, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def do_the_work(input_path: Path, output_path: Path) -> None:
    ...


if __name__ == "__main__":
    sys.exit(main())
```

## `generate_types.py`

The single most important script in this directory. Runs Pydantic-to-TypeScript codegen. Invoked:

- Manually when schemas change (`python scripts/generate_types.py`)
- Automatically via the post-edit hook after any Pydantic model file is modified
- Verified during pre-commit (if staged diff doesn't match what regeneration would produce, commit is blocked)

This script is the mechanism that enforces schema parity between Python and TypeScript. Don't bypass it.

## Blender Scripts

Blender scripts are a special case — they run **inside Blender's Python interpreter**, not the sidecar's. They can `import bpy` but not `import aisc.*`.

Communication with the sidecar happens via:

- **Arguments passed on the command line** (after `--`) for input paths
- **Files written to known output paths** for results
- **Structured logging to stderr** that the sidecar reads and forwards to the app log

Template:

```python
# scripts/blender/render_thumbnail.py
"""
Render a thumbnail for a template with applied textures.

Invoked by the sidecar as:
    blender --background --python scripts/blender/render_thumbnail.py -- <job_spec_path>

Reads the job spec JSON, loads the mesh, applies materials, renders, and writes
the PNG to the path specified in the job spec.
"""

import sys
import json
from pathlib import Path

# bpy is available because we're running inside Blender
import bpy  # type: ignore


def main() -> None:
    # Parse args after the "--" separator
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    job_spec_path = Path(argv[0])
    job = json.loads(job_spec_path.read_text())

    # ... do the rendering ...


if __name__ == "__main__":
    main()
```

## Build Scripts

`build.sh` and `build.ps1` orchestrate a full build:

1. Install Python deps into a fresh venv
2. Bundle the sidecar with `pyoxidizer` or `PyInstaller` (chosen in Phase 0)
3. Run `generate_types.py`
4. Install frontend deps
5. Run frontend build (Vite)
6. Run Tauri build producing the platform installer

Both scripts have identical behavior — they differ only in shell idiom. Keep them in sync when adding steps. If a step is hard to express in one shell but easy in the other, factor it into a Python script and have both shells call the Python script.

## Testing

Scripts have their own test directory: `scripts/tests/`. Focus:

- **Argument parsing** (valid args produce expected behavior, invalid args fail cleanly)
- **Idempotency** (running twice produces same result)
- **Exit codes** (failures exit non-zero)

Scripts that invoke Blender or other subprocesses can't be fully unit tested — test their input/output handling, mock the subprocess invocation.

## Load These Docs When...

- Adding a new script: this file is authoritative
- For `generate_types.py`: `docs/tad/02-data-model.md` §4.6 (TypeScript codegen)
- For Blender rendering: `docs/tad/04-pipelines.md` §6.4 (thumbnail stage)
- For build scripts: `docs/tad/20-deployment.md` (referenced as a section of `docs/tad/16-testing-and-deployment.md`)

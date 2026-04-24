#!/usr/bin/env python
"""
Generate TypeScript types from Pydantic schemas in sidecar/aisc/schemas/.

The single mechanism enforcing schema parity between the Python sidecar and the
TypeScript frontend. Invoked:

  - Manually:  python scripts/generate_types.py
  - Automatically: Claude Code post-edit hook + pre-commit codegen-sync hook

Output:
  - shared-types/index.ts       (TypeScript type definitions)
  - shared-types/package.json   (npm workspace manifest)

Phase 0 bootstrap: no Pydantic schemas exist yet, so this script emits a
near-empty index.ts containing only an `export {}` to make the file a module.

As schemas are added under sidecar/aisc/schemas/, this script will grow to
walk the package, collect every BaseModel subclass, and emit TypeScript
interface / type-alias equivalents. That machinery is deferred to the first
task that introduces a schema (Phase 0 Task 0.5 — project storage).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "shared-types"

INDEX_TS_HEADER = """// AUTO-GENERATED FILE — DO NOT EDIT BY HAND.
// Regenerate with: python scripts/generate_types.py
//
// This file is the source of truth for types that cross the IPC boundary.
// It is derived from the Pydantic schemas in sidecar/aisc/schemas/.
//
// Phase 0 bootstrap: no schemas have been defined yet, so this file is empty.
// It will be populated starting in Phase 0 Task 0.5 (project storage).

export {};
"""

PACKAGE_JSON = """{
  "name": "shared-types",
  "private": true,
  "version": "0.0.0",
  "description": "Auto-generated TypeScript types from Pydantic schemas. Never hand-edit.",
  "types": "index.ts",
  "main": "index.ts"
}
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate TypeScript types from Pydantic schemas."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory (default: shared-types/ at repo root).",
    )
    args = parser.parse_args()

    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        (output_dir / "index.ts").write_text(INDEX_TS_HEADER, encoding="utf-8")
        (output_dir / "package.json").write_text(PACKAGE_JSON, encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: failed to write generated files: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

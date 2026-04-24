"""Sidecar entry point.

Launched by the Tauri host at app start. Hosts the JSON-RPC 2.0 server on
stdio, the async job scheduler, and all pipeline stages.

Phase 0 bootstrap: this is a minimal stub that exits cleanly. The real stdio
JSON-RPC server lands in Phase 0 Task 0.2.
"""

from __future__ import annotations

import asyncio
import sys


async def _serve() -> None:
    """Placeholder for the future stdio JSON-RPC event loop."""
    # Phase 0 Task 0.2 will replace this body with an asyncio server that
    # reads JSON-RPC requests from stdin and writes responses to stdout.
    return None


def run() -> int:
    """Synchronous entry point registered in pyproject.toml `[project.scripts]`."""
    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(run())

"""§13 — write-bytes-then-commit-row artifact ordering.

Artifacts (meshes / images / packages) are files on disk in a canonical layout by
project/item/candidate; Postgres holds only the reference. ``commit_artifact`` enforces the
durability ordering: write the bytes into the canonical layout → ``fsync`` the file AND its
directory → ONLY THEN invoke the repo-owned ``commit_row`` callback. A crash before the row
lands therefore leaves an orphan file (durable bytes), NEVER a row referencing missing bytes.

The mover deliberately holds no DB handle (no engine/session/store parameter): the row is
committed solely by the repo-owned callback (the sole-writer boundary, rule 3).
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from pathlib import Path

_FORBIDDEN_SEGMENTS = frozenset({"", ".", ".."})


def _safe_segment(segment: str) -> str:
    """Reject path segments that could escape the canonical root (rule 4 / §13).

    Phase-2 ids/filenames are sourced from LLM/agent plan output (untrusted); an absolute
    segment would reset the join and ``..``/separators would traverse out of the tree.
    """
    if (
        segment in _FORBIDDEN_SEGMENTS
        or "/" in segment
        or "\\" in segment
        or os.sep in segment
        or (os.altsep is not None and os.altsep in segment)
        or os.path.isabs(segment)
    ):
        raise ValueError(f"unsafe canonical-path segment: {segment!r}")
    return segment


def canonical_path_for(
    root: Path, project_id: str, item_id: str, candidate_id: str, filename: str
) -> Path:
    """The canonical on-disk location for an artifact: root/project/item/candidate/file.

    Every segment is validated (no separators, ``..``, ``.``, empty, or absolute) and the
    resolved path is asserted to stay within ``root`` — a poisoned id can never write outside
    the canonical tree (rule 4).
    """
    parts = [_safe_segment(s) for s in (project_id, item_id, candidate_id, filename)]
    candidate = root.joinpath(*parts)
    if not candidate.resolve().is_relative_to(root.resolve()):  # defense in depth
        raise ValueError(f"canonical path escapes the store root: {candidate}")
    return candidate


async def commit_artifact(
    *,
    scratch_path: Path,
    canonical_path: Path,
    commit_row: Callable[[Path], Awaitable[None]],
) -> Path:
    """Copy scratch bytes into the canonical layout durably, THEN commit the referencing row.

    Ordering guarantee: ``commit_row`` is awaited only after the canonical bytes are fsynced,
    so a failure in ``commit_row`` (a crash stand-in) leaves an orphan file, never a dangling
    row. The scratch file is left in place (sidecar scratch GC is deferred, §20).
    """
    canonical_path.parent.mkdir(parents=True, exist_ok=True)

    data = scratch_path.read_bytes()
    with open(canonical_path, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())

    # fsync the directory so the new dirent itself is durable
    dir_fd = os.open(str(canonical_path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)

    # bytes are durable — only now does the repo layer commit the row
    await commit_row(canonical_path)
    return canonical_path

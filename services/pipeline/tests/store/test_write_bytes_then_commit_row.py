"""RED — §13 write-bytes-then-commit-row artifact ordering.

`commit_artifact` writes the bytes into the canonical layout, fsyncs, and ONLY THEN
invokes the repo-owned `commit_row` callback. A crash at commit time therefore leaves an
orphan file (durable bytes) but NEVER a dangling row referencing missing bytes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import run_sync, sqlite_url


class _SimulatedCrash(RuntimeError):
    """Stand-in for a process death between fsync and row-commit."""


def test_commit_row_runs_only_after_bytes_durable(tmp_path: Path) -> None:
    """spec(§13) — the row callback fires only after the canonical bytes exist on disk."""
    from store.artifacts import canonical_path_for, commit_artifact

    async def _run() -> None:
        scratch = tmp_path / "scratch"
        scratch.mkdir()
        produced = scratch / "mesh.glb"
        produced.write_bytes(b"GEOMDATA")

        canonical_root = tmp_path / "canon"
        dest = canonical_path_for(canonical_root, "p1", "i1", "c1", "mesh.glb")

        seen: dict[str, bool] = {}

        async def commit_row(path: Path) -> None:
            # repo-layer callback: by the time it runs, bytes MUST be durable
            seen["bytes_present_at_commit"] = path.exists()

        result = await commit_artifact(
            scratch_path=produced, canonical_path=dest, commit_row=commit_row
        )

        assert result == dest
        assert dest.exists(), "canonical bytes not written"
        assert seen["bytes_present_at_commit"] is True

    run_sync(_run())


def test_crash_at_commit_leaves_orphan_not_dangling_row(tmp_path: Path) -> None:
    """spec(§13) — a commit-time crash leaves an orphan file, never a dangling row.

    Pinned against a REAL store: the commit callback would persist the row, but it dies
    first — so afterwards the canonical bytes exist (orphan) yet the DB has no row.
    """
    from store.artifacts import canonical_path_for, commit_artifact
    from store.facade import open_store

    async def _run() -> None:
        store = await open_store(sqlite_url(tmp_path), canonical_root=tmp_path / "canon")
        try:
            scratch = tmp_path / "scratch"
            scratch.mkdir()
            produced = scratch / "mesh.glb"
            produced.write_bytes(b"GEOMDATA")

            dest = canonical_path_for(store.canonical_root, "p1", "i1", "c1", "mesh.glb")

            async def crashing_commit(path: Path) -> None:
                # the process dies before the referencing row is committed
                raise _SimulatedCrash("died before COMMIT")

            with pytest.raises(_SimulatedCrash):
                await commit_artifact(
                    scratch_path=produced, canonical_path=dest, commit_row=crashing_commit
                )

            assert dest.exists(), "bytes should be durable (orphan) — the safe failure"
            assert await store.projects.get("p1") is None, "no dangling row may exist"
        finally:
            await store.close()

    run_sync(_run())


@pytest.mark.parametrize("bad_segment", ["..", "/abs", "a/b", "", ".", "a\\b"])
def test_canonical_path_rejects_unsafe_segments(tmp_path: Path, bad_segment: str) -> None:
    """spec(§13, rule 4) — a poisoned id/filename can never escape the canonical root."""
    from store.artifacts import canonical_path_for

    with pytest.raises(ValueError):
        canonical_path_for(tmp_path, bad_segment, "item", "cand", "file.glb")

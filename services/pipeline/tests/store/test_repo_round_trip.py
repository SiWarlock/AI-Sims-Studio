"""RED — §13 repository layer round-trip.

The sidecar repo layer reads/writes the FROZEN domain entities (0.4a) to the store
(sole writer, rule 3). A `Project` written via the repo reads back equal, including the
persisted `schemaVersion` (hybrid persistence: key columns + the full entity as JSONB).
"""

from __future__ import annotations

from pathlib import Path

from aisims_contracts.domain import Project, ProjectState

from .conftest import run_sync, sqlite_url


def test_project_repo_round_trip(tmp_path: Path) -> None:
    """spec(§13) — write a domain entity via the repo, read it back == (incl. schemaVersion)."""
    from store.facade import open_store

    async def _run() -> None:
        store = await open_store(sqlite_url(tmp_path), canonical_root=tmp_path / "canon")
        try:
            project = Project(
                id="proj-y2k",
                name="Y2K Bedroom",
                prompt="a turn-of-the-millennium teen bedroom set",
                desiredItemCount=5,
                status=ProjectState.CREATED,
                schemaVersion=3,  # non-default: proves the value survives dump→JSONB→validate
            )
            await store.projects.put(project)
            got = await store.projects.get("proj-y2k")
        finally:
            await store.close()

        assert got == project
        assert got is not None
        assert got.schemaVersion == 3

    run_sync(_run())


def test_project_repo_get_missing_returns_none(tmp_path: Path) -> None:
    """spec(§13) — a get for an unknown id returns None (no synthetic row)."""
    from store.facade import open_store

    async def _run() -> None:
        store = await open_store(sqlite_url(tmp_path), canonical_root=tmp_path / "canon")
        try:
            assert await store.projects.get("nope") is None
            assert await store.projects.list_ids() == []
        finally:
            await store.close()

    run_sync(_run())

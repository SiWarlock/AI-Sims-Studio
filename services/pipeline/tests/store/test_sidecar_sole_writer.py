"""RED — [SAFETY · rule 3 / forbidden-pattern 4] the sidecar repo layer is the SOLE writer.

Workers write ONLY to sidecar-provided scratch dirs and return paths; they never write
Postgres or the canonical artifact tree. The engine repo layer commits the row AFTER the
worker returns a path. This is the rule-3 enforcement pin (its own commit; security-reviewed).
"""

from __future__ import annotations

import inspect
from pathlib import Path

from aisims_contracts.domain import Project, ProjectState

from .conftest import run_sync, sqlite_url


def test_worker_writes_only_scratch_sidecar_commits_canonical_and_row(tmp_path: Path) -> None:
    """spec(§13/§6, rule 3) — a worker touches only scratch; the sidecar writes canonical + DB."""
    from store.artifacts import canonical_path_for, commit_artifact
    from store.facade import open_store

    async def _run() -> None:
        store = await open_store(sqlite_url(tmp_path), canonical_root=tmp_path / "canon")
        try:
            canonical_root = store.canonical_root
            scratch = tmp_path / "scratch"
            scratch.mkdir()

            # --- WORKER ROLE: handed only a scratch dir, returns a path. No store handle. ---
            def worker(scratch_dir: Path) -> Path:
                out = scratch_dir / "mesh.glb"
                out.write_bytes(b"GEOM")
                return out

            produced = worker(scratch)

            # invariant: the worker wrote ONLY scratch — canonical tree + DB untouched
            assert produced.parent == scratch
            assert not list(canonical_root.rglob("*")) if canonical_root.exists() else True
            assert await store.projects.list_ids() == []

            # --- SIDECAR ROLE: repo layer writes canonical bytes + commits the row ---
            dest = canonical_path_for(canonical_root, "proj-1", "item-1", "cand-1", "mesh.glb")
            project = Project(
                id="proj-1",
                name="Sole Writer",
                prompt="x",
                desiredItemCount=1,
                status=ProjectState.CREATED,
            )

            async def commit_row(path: Path) -> None:
                await store.projects.put(project)

            await commit_artifact(scratch_path=produced, canonical_path=dest, commit_row=commit_row)

            assert dest.exists(), "canonical bytes must be written by the sidecar, not the worker"
            assert await store.projects.get("proj-1") == project
        finally:
            await store.close()

    run_sync(_run())


def test_artifact_mover_cannot_itself_write_the_db(tmp_path: Path) -> None:
    """spec(§13, rule 3) — commit_artifact gets NO engine/session/store; the row is repo-owned.

    Structural pin: the artifact mover can write bytes but must delegate the row to the
    repo-owned `commit_row` callback — it has no parameter through which to reach Postgres.
    """
    from store import artifacts

    sig = inspect.signature(artifacts.commit_artifact)
    params = set(sig.parameters)

    # the row is committed solely by the repo-owned `commit_row` callback
    assert "commit_row" in params, "the row must be delegated to a repo-owned callback"
    # the real safety invariant: the mover holds NO database handle of any kind
    forbidden = {"engine", "session", "sessionmaker", "store", "connection", "conn", "db"}
    assert not (params & forbidden), (
        f"artifact mover must not hold a DB writer; offending params: {params & forbidden}"
    )

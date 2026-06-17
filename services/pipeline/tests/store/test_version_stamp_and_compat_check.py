"""RED — §13 R-i versioning: data-dir/DB version stamp + startup compat check.

A version stamp (schemaVersion + registryVersion + appVersion + dataDirVersion) is
persisted on open; the startup compat check accepts a matching stamp and REFUSES a
mismatched schemaVersion/registryVersion — never silently opens an incompatible store
(forbidden: never DROP a stamp). Migrate-path is the runner (deferred, Q4).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import run_sync, sqlite_url


def test_open_stamps_then_reads_back_matching(tmp_path: Path) -> None:
    """spec(§13) — open persists the current stamp; it reads back equal (never dropped)."""
    from store.facade import open_store
    from store.versioning import CURRENT_STAMP, read_stamp

    async def _run() -> None:
        url = sqlite_url(tmp_path)
        store = await open_store(url, canonical_root=tmp_path / "canon")
        try:
            async with store.sessionmaker() as session:
                stamp = await read_stamp(session)
        finally:
            await store.close()
        assert stamp == CURRENT_STAMP

    run_sync(_run())


def test_check_compat_accepts_match_refuses_mismatch() -> None:
    """spec(§13 R-i) — pure compat verdict: OK on match, REFUSE on version mismatch."""
    from store.versioning import CURRENT_STAMP, CompatVerdict, check_compat

    assert check_compat(CURRENT_STAMP) is CompatVerdict.OK

    bumped = CURRENT_STAMP.model_copy(update={"schemaVersion": CURRENT_STAMP.schemaVersion + 1})
    assert check_compat(bumped) is CompatVerdict.REFUSE

    bumped_reg = CURRENT_STAMP.model_copy(
        update={"registryVersion": CURRENT_STAMP.registryVersion + 1}
    )
    assert check_compat(bumped_reg) is CompatVerdict.REFUSE


def test_open_refuses_incompatible_store(tmp_path: Path) -> None:
    """spec(§13 R-i) — re-opening a store stamped with a mismatched version is refused."""
    from store.facade import open_store
    from store.versioning import CURRENT_STAMP, IncompatibleStoreError, write_stamp

    async def _run() -> None:
        url = sqlite_url(tmp_path)
        canon = tmp_path / "canon"
        store = await open_store(url, canonical_root=canon)  # first open stamps CURRENT
        try:
            async with store.sessionmaker() as session:
                await write_stamp(
                    session,
                    CURRENT_STAMP.model_copy(
                        update={"schemaVersion": CURRENT_STAMP.schemaVersion + 1}
                    ),
                )
                await session.commit()
        finally:
            await store.close()

        with pytest.raises(IncompatibleStoreError):
            await open_store(url, canonical_root=canon, enforce_compat=True)

    run_sync(_run())

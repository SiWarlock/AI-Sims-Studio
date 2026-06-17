"""§13 R-i — data-store version stamp + startup compatibility check.

The store records a ``VersionStamp`` (schema / registry / app / data-dir versions) in the
singleton ``schema_meta`` row on first open. On a later open the startup compat check
compares the stored stamp to the current one and REFUSES (``IncompatibleStoreError``) on a
``schemaVersion``/``registryVersion`` mismatch — never silently opening an incompatible
store. The migrate path (the runner) is deferred (Q4); the stamp is never dropped.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SchemaMetaRow

_STAMP_ID = 1

# Current store versions. schemaVersion mirrors the persisted-entity contract (0.4a);
# registryVersion tracks the open-registry schema; appVersion/dataDirVersion stamp the build.
SCHEMA_VERSION = 1
REGISTRY_VERSION = 1
APP_VERSION = "0.0.0"
DATA_DIR_VERSION = 1


class VersionStamp(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schemaVersion: int
    registryVersion: int
    appVersion: str
    dataDirVersion: int


CURRENT_STAMP = VersionStamp(
    schemaVersion=SCHEMA_VERSION,
    registryVersion=REGISTRY_VERSION,
    appVersion=APP_VERSION,
    dataDirVersion=DATA_DIR_VERSION,
)


class CompatVerdict(Enum):
    OK = "ok"
    REFUSE = "refuse"


class IncompatibleStoreError(RuntimeError):
    """Raised on open when the stored stamp is incompatible with the current build."""

    def __init__(self, stored: VersionStamp, current: VersionStamp) -> None:
        super().__init__(f"incompatible store: stored={stored!r} current={current!r}")
        self.stored = stored
        self.current = current


def check_compat(stamp: VersionStamp, current: VersionStamp = CURRENT_STAMP) -> CompatVerdict:
    """REFUSE on a schema/registry version mismatch; OK otherwise (app/data-dir are advisory)."""
    if (
        stamp.schemaVersion != current.schemaVersion
        or stamp.registryVersion != current.registryVersion
    ):
        return CompatVerdict.REFUSE
    return CompatVerdict.OK


async def read_stamp(session: AsyncSession) -> VersionStamp | None:
    row = await session.get(SchemaMetaRow, _STAMP_ID)
    if row is None:
        return None
    return VersionStamp(
        schemaVersion=row.schema_version,
        registryVersion=row.registry_version,
        appVersion=row.app_version,
        dataDirVersion=row.data_dir_version,
    )


async def write_stamp(session: AsyncSession, stamp: VersionStamp) -> None:
    """Upsert the singleton stamp row. Caller commits (open_store does; tests do explicitly)."""
    await session.merge(
        SchemaMetaRow(
            id=_STAMP_ID,
            schema_version=stamp.schemaVersion,
            registry_version=stamp.registryVersion,
            app_version=stamp.appVersion,
            data_dir_version=stamp.dataDirVersion,
        )
    )

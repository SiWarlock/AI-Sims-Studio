"""The §8 structural-GEOM validator — the "fast GEOM check before packaging".

ARCHITECTURE §8: *"GEOM export = a distinct stage with immediate structural validation (fast GEOM
check before packaging — fail at GEOM, not at install)."* This module is that gate: a fail-soft
fast reject that turns malformed GEOM bytes into a structured :class:`GeomStructResult` — **never**
an exception (a bad mesh must surface as a GEOM-stage failure, not a crash). It is real, reusable
Phase-4 infra — not throwaway spike glue.

⚠️ **SPIKE / PLACEHOLDER container format (S1a).** Until a real Sims 4 donor is available, this
parses a *documented synthetic spike-GEOM container* (see :data:`GEOM_HEADER`): the **real**
``GEOM`` FourCC magic, then a fixed little-endian header carrying the salient §8 structural fields
(version, vertex / face / meshgroup counts, UV-set flags, a declared trailing-body length). The
synthetic fixture in ``tests/fixtures`` writes this exact layout, so the validator is genuinely
test-first today — but a green *positive* path proves harness wiring, **not** real-EA-GEOM
acceptance; the negative paths (bad magic / truncation / bad counts) carry the validation weight.
The byte-exact real-EA-donor GEOM / RCOL parse + a real donor-extracted ``.geom`` fixture are the
**env-ready swap** (the S1a env-ready probe); that distinction lands explicitly in the S1 verdict.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Final

# The real Sims 4 GEOM resource FourCC tag (RCOL chunk magic) — stable across the spike → env-ready
# swap. The header AFTER it is the SPIKE placeholder layout (see the module docstring).
GEOM_MAGIC: Final = b"GEOM"
# magic(4s) · version(I) · vertices(I) · faces(I) · meshgroups(I) · uvSets(I) · bodyLen(I) — LE.
GEOM_HEADER: Final = struct.Struct("<4sIIIIII")
GEOM_HEADER_SIZE: Final = GEOM_HEADER.size
# A GEOM version far outside any plausible EA range signals a misread / garbage blob.
_MAX_SANE_VERSION: Final = 0xFFFF


@dataclass(frozen=True, slots=True)
class GeomStructIssue:
    """One structural defect. ``kind`` ∈ {truncated, magic, version, counts, parse}."""

    kind: str
    detail: str


@dataclass(frozen=True, slots=True)
class GeomStructResult:
    """The fast-check outcome: ``ok`` plus the extracted counts / UV flags the §8 game-ready gate
    and the §9 packager consume. On a reject, ``issues`` carries the structured reasons."""

    ok: bool
    issues: tuple[GeomStructIssue, ...] = ()
    vertices: int = 0
    faces: int = 0
    meshgroups: int = 0
    uv0: bool = False
    uv1: bool = False


def _reject(kind: str, detail: str) -> GeomStructResult:
    return GeomStructResult(ok=False, issues=(GeomStructIssue(kind, detail),))


def validate_geom_structure(data: bytes) -> GeomStructResult:
    """Fast structural check on GEOM bytes (§8). Returns ``ok=True`` + counts for a structurally
    valid container; otherwise ``ok=False`` + structured issues. **Never raises** on malformed
    input — every byte sequence yields a :class:`GeomStructResult`."""
    try:
        if len(data) == 0:
            return _reject("truncated", "empty input: no GEOM bytes")
        if len(data) < GEOM_HEADER_SIZE:
            return _reject("truncated", f"need >= {GEOM_HEADER_SIZE} header bytes, got {len(data)}")

        magic, version, vertices, faces, meshgroups, uv_sets, body_len = GEOM_HEADER.unpack_from(
            data, 0
        )
        if magic != GEOM_MAGIC:
            return _reject("magic", f"bad magic {magic!r}, expected {GEOM_MAGIC!r}")

        issues: list[GeomStructIssue] = []
        if version == 0 or version > _MAX_SANE_VERSION:
            issues.append(GeomStructIssue("version", f"implausible GEOM version {version}"))
        if len(data) < GEOM_HEADER_SIZE + body_len:
            have = len(data) - GEOM_HEADER_SIZE
            issues.append(GeomStructIssue("truncated", f"declared body {body_len}, have {have}"))
        if vertices == 0 or faces == 0 or meshgroups < 1:
            issues.append(
                GeomStructIssue(
                    "counts", f"vertices={vertices} faces={faces} meshgroups={meshgroups}"
                )
            )

        return GeomStructResult(
            ok=not issues,
            issues=tuple(issues),
            vertices=int(vertices),
            faces=int(faces),
            meshgroups=int(meshgroups),
            uv0=bool(uv_sets & 0b01),
            uv1=bool(uv_sets & 0b10),
        )
    except Exception as exc:  # fail-soft (§8): malformed bytes never crash the GEOM stage
        return _reject("parse", f"unparseable GEOM bytes: {exc!r}")

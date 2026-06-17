"""Synthetic GEOM fixture builder for the S1a spike (headless, no Blender).

The spike's structural validator (``geom/structural.py``) parses a documented, little-endian
*spike GEOM container* whose header carries the real GEOM FourCC magic (``b"GEOM"``) plus the
salient §8 structural fields (version, vertex / face / meshgroup counts, UV-set flags). This
builder emits exactly that container — sharing the validator's own ``GEOM_HEADER`` layout as the
single source of truth — so the validator is genuinely test-first today.

The byte-exact real-EA-donor GEOM / RCOL parse + a real donor-extracted ``.geom`` fixture are the
**env-ready swap** (the S1a env-ready follow-up); see
``docs/briefs/spikes-001-1.1-s1a-geom-harness.md``. Until then the positive path is intentionally
"writer and reader share one layout" — the negative paths (bad magic / truncation / bad counts)
are where the validator's reject logic earns its keep headless.
"""

from __future__ import annotations

from geom.structural import GEOM_HEADER, GEOM_MAGIC


def make_geom_bytes(
    *,
    magic: bytes = GEOM_MAGIC,
    version: int = 12,
    vertices: int = 8,
    faces: int = 12,
    meshgroups: int = 1,
    uv0: bool = True,
    uv1: bool = True,
    body: bytes = b"\x00" * 16,
    body_len: int | None = None,
) -> bytes:
    """Pack a synthetic spike-GEOM container.

    ``body_len`` defaults to ``len(body)``; pass a larger value to forge a *declared-body-
    truncated* fixture (the validator must reject it without reading past the buffer).
    """
    uv_sets = (0b01 if uv0 else 0) | (0b10 if uv1 else 0)
    declared = len(body) if body_len is None else body_len
    header = GEOM_HEADER.pack(
        magic[:4].ljust(4, b"\x00"),
        version,
        vertices,
        faces,
        meshgroups,
        uv_sets,
        declared,
    )
    return header + body

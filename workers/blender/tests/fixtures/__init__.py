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

import struct

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


# --- REAL Sims-4 GEOM (0x015A1849) minimal container ---------------------------------------------
# A hand-built minimal instance of the *real* EA GEOM/RCOL chunk, per the SimsWiki 0x015A1849 spec
# (the format authority — Context7 has no @s4tk/GEOM coverage, confirmed spikes-001). This drives
# the real-format validator (``geom/real_geom.py``) test-first; the env-ready arm captures a real
# bpy-emitted ``.geom`` and asserts the SAME validator accepts it (run-and-observe).
# Default = a v0x05 cube: Position + Normal + one UV element, 8 verts, 36 face-points.
# KEEP IN SYNC with `_FORMATS` in blender_scripts/geom_export.py (different interpreter — mirrored).
_DEFAULT_FORMATS: tuple[tuple[int, int, int], ...] = (
    (1, 1, 12),  # dataType 1 = Position, subType 1 = floats, 3x4 bytes
    (2, 1, 12),  # dataType 2 = Normal
    (3, 1, 8),  # dataType 3 = UV (uv_0), 2x4 bytes
)


def make_real_geom_bytes(
    *,
    magic: bytes = GEOM_MAGIC,
    version: int = 0x05,
    num_verts: int = 8,
    formats: tuple[tuple[int, int, int], ...] = _DEFAULT_FORMATS,
    num_face_points: int = 36,
    embedded_id: int = 0,
) -> bytes:
    """Pack a minimal real-format Sims-4 GEOM (0x015A1849) chunk.

    Each ``formats`` entry is ``(dataType, subType, bytesPerElement)``; a ``dataType == 3`` element
    is a UV set. ``embedded_id == 0`` means no MTNF material block. Vertex/index payloads are zero-
    filled (the structural check only reads counts + the vertex-format descriptor, never the data).
    """
    stride = sum(bpe for (_, _, bpe) in formats)
    out = bytearray()
    out += magic[:4].ljust(4, b"\x00")
    out += struct.pack("<I", version)
    out += struct.pack("<II", 0, 0)  # tgiOffset, tgiSize (empty trailing TGI list)
    out += struct.pack("<I", embedded_id)
    if embedded_id != 0:
        out += struct.pack("<I", 0)  # MTNF chunkSize (empty material)
    out += struct.pack("<II", 0, 0)  # mergeGroup, sortOrder
    out += struct.pack("<I", num_verts)
    out += struct.pack("<I", len(formats))
    for data_type, sub_type, bpe in formats:
        out += struct.pack("<IIB", data_type, sub_type, bpe)
    out += b"\x00" * (num_verts * stride)  # vertex data
    out += struct.pack("<I", 1)  # itemCount
    out += struct.pack("<B", 2)  # bytesPerFacePoint (WORD indices)
    out += struct.pack("<I", num_face_points)
    out += b"\x00" * (num_face_points * 2)  # index data
    out += struct.pack("<I", 0)  # skinControllerIndex (v0x05 tail)
    out += struct.pack("<I", 0)  # boneCount
    out += struct.pack("<I", 0)  # trailing TGI list count (empty)
    return bytes(out)

"""Real Sims-4 GEOM (0x015A1849) validator — the env-ready swap of the spike placeholder parser.

Parses the genuine EA GEOM/RCOL chunk per the **SimsWiki `0x015A1849`** spec (the format authority —
Context7 has no @s4tk/GEOM coverage, confirmed spikes-001). Minimal structural check (Q2 option a):
the real ``GEOM`` magic + a real version (0x05 / 0x0C) + non-empty vertex / face-point / meshgroup
counts + a UV vertex-format element (dataType 3). Fail-soft: never raises — every input yields a
:class:`~geom.structural.GeomStructResult`.

Distinct from ``geom/structural.py`` (the spike PLACEHOLDER container parser): this one rejects that
placeholder, proving it parses genuine EA GEOM. The PASS bar here is **structural validity only** —
full @s4tk round-trip is S1b, in-game placeability is S1c.
"""

from __future__ import annotations

import struct
from typing import Final

from geom.structural import GEOM_MAGIC, GeomStructIssue, GeomStructResult

_VALID_VERSIONS: Final = (0x05, 0x0C)
_MAX_FCOUNT: Final = 64  # sane cap on the vertex-format element count (desync / garbage guard)
_MAX_COUNT: Final = 1 << 28  # sane cap on vertex / face-point counts
_UV_DATATYPE: Final = 3  # GEOM vertex-format dataType 3 = a UV set


class _Reader:
    """A bounds-checked little-endian cursor; a read past the buffer raises ``ValueError``."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    def u8(self) -> int:
        return self._take(1)[0]

    def u32(self) -> int:
        return int(struct.unpack_from("<I", self._take(4))[0])

    def take(self, n: int) -> bytes:
        return self._take(n)

    def skip(self, n: int) -> None:
        """Advance past ``n`` bytes WITHOUT materializing a slice (discard paths) — bounds-checked
        so an attacker-declared length still fails closed, but never amplifies memory."""
        if n < 0 or self._pos + n > len(self._data):
            raise ValueError(f"skip of {n} past buffer at {self._pos}/{len(self._data)}")
        self._pos += n

    def _take(self, n: int) -> bytes:
        if n < 0 or self._pos + n > len(self._data):
            raise ValueError(f"read of {n} past buffer at {self._pos}/{len(self._data)}")
        chunk = self._data[self._pos : self._pos + n]
        self._pos += n
        return chunk


def _issue(kind: str, detail: str) -> GeomStructResult:
    return GeomStructResult(ok=False, issues=(GeomStructIssue(kind, detail),))


def validate_real_geom(data: bytes) -> GeomStructResult:
    """Structural check on REAL Sims-4 GEOM bytes (§8). Returns ``ok=True`` + counts for a valid
    GEOM chunk; otherwise ``ok=False`` + structured issues. **Never raises** on malformed input."""
    try:
        return _parse(data)
    except (ValueError, struct.error, IndexError) as exc:
        return _issue("parse", f"unparseable GEOM bytes: {exc!r}")


def _parse(data: bytes) -> GeomStructResult:
    r = _Reader(data)
    if r.take(4) != GEOM_MAGIC:
        return _issue("magic", "not a GEOM chunk")
    version = r.u32()
    if version not in _VALID_VERSIONS:
        return _issue("version", f"unknown GEOM version {version:#x}")

    r.u32()  # tgiOffset
    r.u32()  # tgiSize
    embedded_id = r.u32()
    if embedded_id != 0:
        r.skip(r.u32())  # skip the MTNF material block (declared chunkSize)
    r.u32()  # mergeGroup
    r.u32()  # sortOrder

    num_verts = r.u32()
    if num_verts > _MAX_COUNT:  # cap co-located with the read (matches the eager FCount check)
        return _issue("counts", f"implausible numVerts {num_verts}")
    fcount = r.u32()
    if fcount == 0 or fcount > _MAX_FCOUNT:
        return _issue("counts", f"implausible FCount {fcount}")
    stride = 0
    uv_elements = 0
    for _ in range(fcount):
        data_type = r.u32()
        r.u32()  # subType
        stride += r.u8()  # bytesPerElement
        if data_type == _UV_DATATYPE:
            uv_elements += 1
    r.skip(num_verts * stride)  # skip the vertex data block (bounds-checked, no slice copy)

    item_count = r.u32()
    if item_count == 0 or item_count > _MAX_FCOUNT:
        return _issue("counts", f"implausible itemCount {item_count}")
    num_face_points = 0
    for _ in range(item_count):
        bytes_per_fp = r.u8()
        nfp = r.u32()
        if nfp > _MAX_COUNT:
            return _issue("counts", f"implausible numFacePoints {nfp}")
        num_face_points += nfp
        r.skip(nfp * bytes_per_fp)  # skip the index data (bounds-checked, no slice copy)

    issues: list[GeomStructIssue] = []
    if num_verts == 0:
        issues.append(GeomStructIssue("counts", "zero vertices"))
    if num_face_points == 0:
        issues.append(GeomStructIssue("counts", "zero face-points"))
    if uv_elements == 0:
        issues.append(GeomStructIssue("uv", "no UV vertex-format element"))
    return GeomStructResult(
        ok=not issues,
        issues=tuple(issues),
        vertices=num_verts,
        faces=num_face_points // 3,
        meshgroups=1,  # one GEOM chunk = one mesh group
        uv0=uv_elements >= 1,
        uv1=uv_elements >= 2,
    )

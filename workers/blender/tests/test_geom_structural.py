"""RED tests for the §8 structural-GEOM validator (S1a) — `geom/structural.py`.

§8: "GEOM export = a distinct stage with immediate structural validation (fast GEOM check before
packaging — fail at GEOM, not at install)." The validator is a fail-soft fast reject: malformed
bytes surface as a structured ``GeomStructResult``, never an exception.
"""

from __future__ import annotations

import pytest

from geom.structural import GeomStructResult, validate_geom_structure
from tests.fixtures import make_geom_bytes


def test_validate_geom_rejects_empty() -> None:
    # spec(§8): empty input is a soft reject (fail at GEOM, not at install), never a raise.
    result = validate_geom_structure(b"")
    assert result.ok is False
    assert result.issues
    assert result.issues[0].kind == "truncated"


def test_validate_geom_rejects_bad_magic() -> None:
    # spec(§8): structural validation is a real gate — a non-GEOM blob is rejected on magic.
    result = validate_geom_structure(make_geom_bytes(magic=b"XXXX"))
    assert result.ok is False
    assert any(issue.kind == "magic" for issue in result.issues)


def test_validate_geom_rejects_truncated() -> None:
    # spec(§8): valid magic + header but a body cut short past the declared length → soft reject.
    truncated = make_geom_bytes(body=b"\x00" * 4, body_len=256)
    result = validate_geom_structure(truncated)
    assert result.ok is False
    assert any(issue.kind == "truncated" for issue in result.issues)


def test_validate_geom_accepts_minimal_fixture() -> None:
    # spec(§8): a structurally valid GEOM yields the counts + UV flags the gate / §9 packager need.
    result = validate_geom_structure(
        make_geom_bytes(vertices=8, faces=12, meshgroups=1, uv0=True, uv1=True)
    )
    assert result.ok is True
    assert result.vertices > 0
    assert result.faces > 0
    assert result.meshgroups >= 1
    assert result.uv0 is True
    assert result.uv1 is True


@pytest.mark.parametrize(
    "geom",
    [
        make_geom_bytes(vertices=0),
        make_geom_bytes(faces=0),
        make_geom_bytes(meshgroups=0),
    ],
)
def test_validate_geom_rejects_zero_counts(geom: bytes) -> None:
    # spec(§8): zero vertices / faces or no meshgroup → a `counts` reject (the gate / §9 packager
    # need real geometry, not an empty shell).
    result = validate_geom_structure(geom)
    assert result.ok is False
    assert any(issue.kind == "counts" for issue in result.issues)


def test_validate_geom_rejects_version_zero() -> None:
    # spec(§8): version 0 is implausible → a `version` issue (a misread / garbage header).
    result = validate_geom_structure(make_geom_bytes(version=0))
    assert result.ok is False
    assert any(issue.kind == "version" for issue in result.issues)


def test_validate_geom_accepts_max_version_boundary() -> None:
    # spec(§8): the inclusive upper version bound (0xFFFF) must still pass (boundary, not a reject).
    result = validate_geom_structure(make_geom_bytes(version=0xFFFF))
    assert result.ok is True


@pytest.mark.parametrize(
    "blob",
    [
        b"",
        b"G",
        b"GEO",
        b"GEOM",
        b"GEOM\x00\x00",
        b"\x00" * 5,
        b"\xff" * 40,
        b"GEOM" + b"\x01" * 3,
        bytes(range(50)),
    ],
)
def test_validate_geom_never_raises_on_fuzz(blob: bytes) -> None:
    # spec(§8): fail-soft — every input yields a GeomStructResult; a malformed mesh never crashes.
    result = validate_geom_structure(blob)
    assert isinstance(result, GeomStructResult)

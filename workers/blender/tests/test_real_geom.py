"""RED tests for the REAL Sims-4 GEOM (0x015A1849) structural validator — `geom/real_geom.py`.

§8 real-format structural validation: the env-ready swap of the spikes-001 *placeholder* parser.
This validator parses the genuine EA GEOM/RCOL chunk (SimsWiki 0x015A1849: magic → version 0x05/0x0C
→ tgi → embeddedID(+MTNF) → mergeGroup/sortOrder → numVerts → vertex-format descriptor → vertex data
→ itemCount/numFacePoints → tail). It must accept a real GEOM, reject the spikes-001 placeholder
(proving it really parses EA GEOM, not the synthetic container), and never raise on garbage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from geom.real_geom import validate_real_geom
from geom.structural import GeomStructResult
from tests.fixtures import make_geom_bytes, make_real_geom_bytes

_FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_real_geom_structural_accepts_minimal_fixture() -> None:
    # spec(§8): a valid real GEOM → ok=True + the counts/UV the gate / §9 packager need.
    result = validate_real_geom(make_real_geom_bytes())
    assert result.ok is True
    assert result.vertices == 8
    assert result.faces == 12  # 36 face-points / 3
    assert result.meshgroups >= 1
    assert result.uv0 is True


def test_real_geom_structural_accepts_captured_fixture() -> None:
    # spec(§8): the REAL Blender-emitted GEOM — captured from the headless probe (blender 5.1.2 on
    # Apple Silicon) — passes the SAME validator, proving it works on real Blender output, not just
    # the hand-built fixture. This pins the run-and-observe result of the S1a env-ready emission.
    data = (_FIXTURE_DIR / "cube_v0x05.geom").read_bytes()
    result = validate_real_geom(data)
    assert result.ok is True
    assert result.vertices > 0
    assert result.faces > 0
    assert result.uv0 is True


def test_real_geom_structural_accepts_version_0x0c() -> None:
    # spec(§8): the version-field check accepts 0x0C. NOTE: the fixture emits a v0x05 byte layout
    # with only the version field overwritten — the parser intentionally stops before the
    # version-dependent tail, so this pins version acceptance, not a full v0x0C tail layout.
    result = validate_real_geom(make_real_geom_bytes(version=0x0C))
    assert result.ok is True


def test_real_geom_structural_flags_missing_uv() -> None:
    # spec(§8): a GEOM with no UV element → ok=False with a `uv` issue (the gate needs UVs).
    no_uv = make_real_geom_bytes(formats=((1, 1, 12), (2, 1, 12)))
    result = validate_real_geom(no_uv)
    assert result.ok is False
    assert any(issue.kind == "uv" for issue in result.issues)


def test_real_geom_structural_rejects_placeholder_and_garbage() -> None:
    # spec(§8): the real parser must REJECT the spikes-001 placeholder container and random bytes —
    # proving it parses genuine EA GEOM, not the synthetic spike layout. Never raises.
    placeholder = make_geom_bytes()
    assert validate_real_geom(placeholder).ok is False
    for blob in (b"", b"GEOM", b"GEOM\x99\x00\x00\x00", b"\xff" * 64, bytes(range(80))):
        result = validate_real_geom(blob)
        assert isinstance(result, GeomStructResult)
        assert result.ok is False


@pytest.mark.parametrize(
    "blob",
    [b"", b"G", b"GEOM", b"GEOM" + b"\x05\x00\x00\x00", b"\x00" * 4, b"\xab" * 200],
)
def test_real_geom_never_raises_on_fuzz(blob: bytes) -> None:
    # spec(§8): fail-soft — every input yields a GeomStructResult, never an exception.
    assert isinstance(validate_real_geom(blob), GeomStructResult)

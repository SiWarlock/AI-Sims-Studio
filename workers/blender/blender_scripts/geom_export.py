# mypy: ignore-errors
# ^ Runs under Blender's bundled Python (bpy/bmesh available there, not the worker uv env), so it is
#   excluded from mypy --strict (inline directive + the blender_scripts/ pyproject exclude).
"""bpy GEOM-emission script for the S1a env-ready probe (runs under Blender's bundled Python).

Invoked headless::

    blender --background --factory-startup --python blender_scripts/geom_export.py -- <jobfile>

Reads the ``BlenderJob`` job-file, builds a trivial **cube**, and writes a minimal **real** Sims-4
GEOM (0x015A1849, version 0x05) chunk + the worker result-file into the job-file's scratch dir. This
is the **custom minimal GEOM writer** (the §20 fallback) — a structural-first signal, NOT a
game-ready GEOM (no LODs / shadow mesh / real unwrap — those are Phase-4). Byte layout per the
SimsWiki ``0x015A1849`` spec. **EXPLORATORY** — may be rewritten once the method is proven.

Runs under Blender's bundled Python 3.13 (``bpy`` available); it is NOT part of the worker uv env /
import graph (mypy-excluded) and imports no worker modules (different interpreter + sys.path).
"""

import json
import struct
import sys
from pathlib import Path

import bmesh
import bpy

_GEOM_MAGIC = b"GEOM"
_GEOM_VERSION = 0x05
# vertex-format descriptor: (dataType, subType, bytesPerElement) — Position, Normal, UV(uv_0).
# KEEP IN SYNC with `_DEFAULT_FORMATS` in tests/fixtures/__init__.py (different interpreter — the
# bpy script can't import the worker uv env, so the layout is mirrored, not shared).
_FORMATS = ((1, 1, 12), (2, 1, 12), (3, 1, 8))


def _argv_after_ddash() -> list[str]:
    argv = sys.argv
    return argv[argv.index("--") + 1 :] if "--" in argv else []


def _build_cube() -> bpy.types.Mesh:
    """Build a triangulated unit cube with a uv_0 layer (deterministic; no GUI / startup deps)."""
    mesh = bpy.data.meshes.new("spike_cube")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])  # GEOM faces are triangles
    uv_layer = bm.loops.layers.uv.new("uv_0")
    for face in bm.faces:
        for loop in face.loops:
            # trivial planar UV from XY (structural-only; real unwrap is Phase-4)
            loop[uv_layer].uv = (loop.vert.co.x + 0.5, loop.vert.co.y + 0.5)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _serialize_geom(mesh: bpy.types.Mesh) -> bytes:
    """Pack the mesh into a minimal real Sims-4 GEOM v0x05 chunk (SimsWiki 0x015A1849)."""
    num_verts = len(mesh.vertices)
    uv_by_vert = [(0.0, 0.0)] * num_verts
    uv_data = mesh.uv_layers.active
    if uv_data is not None:
        for loop in mesh.loops:
            uv = uv_data.data[loop.index].uv
            uv_by_vert[loop.vertex_index] = (uv[0], uv[1])

    out = bytearray()
    out += _GEOM_MAGIC
    out += struct.pack("<I", _GEOM_VERSION)
    out += struct.pack("<II", 0, 0)  # tgiOffset, tgiSize
    out += struct.pack("<I", 0)  # embeddedID (no MTNF material)
    out += struct.pack("<II", 0, 0)  # mergeGroup, sortOrder
    out += struct.pack("<I", num_verts)
    out += struct.pack("<I", len(_FORMATS))
    for data_type, sub_type, bpe in _FORMATS:
        out += struct.pack("<IIB", data_type, sub_type, bpe)
    for vert in mesh.vertices:
        co, normal = vert.co, vert.normal
        uv = uv_by_vert[vert.index]
        out += struct.pack("<3f", co.x, co.y, co.z)
        out += struct.pack("<3f", normal.x, normal.y, normal.z)
        out += struct.pack("<2f", uv[0], uv[1])

    indices: list[int] = []
    for poly in mesh.polygons:
        indices.extend(poly.vertices[:3])  # triangulated → 3 verts per poly
    out += struct.pack("<I", 1)  # itemCount
    out += struct.pack("<B", 2)  # bytesPerFacePoint (uint16 indices)
    out += struct.pack("<I", len(indices))  # numFacePoints
    for idx in indices:
        out += struct.pack("<H", idx)
    out += struct.pack("<I", 0)  # skinControllerIndex (v0x05 tail)
    out += struct.pack("<I", 0)  # boneCount
    out += struct.pack("<I", 0)  # trailing TGI list count (empty)
    return bytes(out)


def main() -> int:
    args = _argv_after_ddash()
    if not args:
        print("GEOM_EXPORT_ERROR: no job-file path after --", file=sys.stderr)
        return 2
    jobfile = Path(args[0])
    scratch = jobfile.parent
    job = json.loads(jobfile.read_text())
    job_id = str(job.get("jobId", "job"))
    result_path = scratch / f"{job_id}.result.json"

    mesh = _build_cube()
    num_verts = len(mesh.vertices)
    # The minimal writer packs uint16 ('<H') face indices — guard the cap so an over-large mesh
    # yields a clean FAILED result-file the harness can report, not an opaque non-zero crash.
    if num_verts > 0xFFFF:
        result_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "error": {
                        "code": "GEOM_EXPORT_FAILED",
                        "category": "geometry",
                        "retryable": False,
                        "creatorMessage": "The mesh is too large for the spike GEOM writer.",
                        "maintainerDetail": f"numVerts {num_verts} exceeds the uint16 index cap",
                    },
                }
            )
        )
        print(f"GEOM_EXPORT_ERROR: too many verts {num_verts}", file=sys.stderr)
        return 1

    geom = _serialize_geom(mesh)
    geom_path = scratch / f"{job_id}.geom"
    geom_path.write_bytes(geom)

    result_path.write_text(
        json.dumps(
            {
                "status": "succeeded",
                "geomBytesRef": str(geom_path),
                "gateMetrics": {
                    "normals": True,
                    "uv": True,
                    "lods": 0,
                    "polyByTile": {},
                    "meshgroups": 1,
                },
                "previewRef": None,
            }
        )
    )
    print(f"GEOM_EMITTED bytes={len(geom)} verts={num_verts} path={geom_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

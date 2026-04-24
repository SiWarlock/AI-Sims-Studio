# DBPF Library Adapter — Claude Code Guidance

You are working inside `sidecar/aisc/dbpf_lib/`. This package is the **sole interface to DBPF file format operations** in the project. Nothing outside this package reads or writes `.package` files.

Reminder: `sidecar/CLAUDE.md` and `CODING_STANDARDS.md` set the general rules. This file covers rules specific to DBPF work.

## Purpose of This Package

DBPF (Database Packed File) is the container format for Sims 4 `.package` files. It has a specific binary layout, TGI (Type-Group-Instance) resource IDs, and compression rules. Getting any of this wrong produces files Sims 4 refuses to load or corrupts existing saves.

This package isolates all that complexity behind a clean interface so the rest of the codebase never has to think about bytes.

## The Interface

```python
# sidecar/aisc/dbpf_lib/__init__.py (public API)

class TGI(BaseModel):
    type_id: int
    group_id: int
    instance_id: int

class DBPFReader(Protocol):
    def open(self, path: Path) -> None: ...
    def list_resources(self) -> list[TGI]: ...
    def read_resource(self, tgi: TGI) -> bytes: ...
    def close(self) -> None: ...

class DBPFWriter(Protocol):
    def open(self, path: Path) -> None: ...
    def add_resource(self, tgi: TGI, data: bytes) -> None: ...
    def close(self) -> None: ...

def open_reader(path: Path) -> DBPFReader: ...
def open_writer(path: Path) -> DBPFWriter: ...
```

The underlying implementation (external library vs custom, decided by D-1 in Phase 1 POC) is a detail. Never let implementation types leak outside this package.

## Hard Rules

1. **Determinism is non-negotiable.** The same inputs in the same order must produce a byte-identical `.package` file. This is tested (see `tests/dbpf_lib/test_determinism.py`) and enforced for `admin.rebuild` functionality (MVP-AC-020 and MVP-AC-029).
2. **Resource order is canonical.** Resources are written to the DBPF in sorted TGI order. Never order by insertion time or any other non-deterministic basis.
3. **TGI generation is deterministic.** IDs come from stable hashes of `(project_id, item_id, resource_kind[, swatch_index])`. See `sidecar/aisc/packaging/tgi.py`. This package never generates TGIs — it only writes or reads them.
4. **No AI in this package.** AI never influences DBPF bytes, TGI assignment, or resource order. DBPF is a deterministic pipeline.
5. **Writes are atomic.** Write to a temp file in the target directory, then rename. If a write fails partway through, the target file is unchanged.
6. **Byte order matters.** DBPF uses little-endian for all numeric fields. `struct.pack` with explicit `<` prefix. No host-endian assumptions.
7. **Resources are opaque bytes to this package.** Decoding of meshes, textures, tuning, etc., happens elsewhere. This package moves bytes in and out.
8. **No streaming writes for MVP.** Full buffering is acceptable given our collection size cap. If we ever need to handle huge collections, streaming can be added, but MVP prioritizes determinism simplicity over peak memory efficiency.

## File Structure

```
dbpf_lib/
├── __init__.py              # public API (Protocols + factory functions)
├── reader.py                # DBPFReader implementation
├── writer.py                # DBPFWriter implementation
├── header.py                # DBPF header struct (index position, resource count)
├── index.py                 # index entry layout
├── compression.py           # RefPack / QFS compression for specific resource types
├── tgi.py                   # TGI parsing/serialization (NOT generation — see packaging/tgi.py)
└── tests/
    └── test_determinism.py  # critical: identical inputs → identical bytes
```

## Compression

Some resource types in DBPF are compressed with RefPack (also called QFS). The rules:

- **Tuning XML:** may or may not be compressed; readers must handle both.
- **DDS textures:** already DXT-compressed; do not additionally RefPack-compress.
- **Mesh resources:** follow the base-game convention (check compression flag in the index entry).
- **Catalog entries:** uncompressed.

Compression is an `index_entry.flags` concern. When writing, match the base-game convention for each resource type. When reading, decompress if the flag indicates.

## TGI ID Semantics

For reference (TGI generation happens outside this package):

- **Type ID:** identifies the resource kind (mesh, diffuse texture, catalog entry, tuning, STBL, thumbnail). Fixed constants per kind. Defined in `sidecar/aisc/packaging/resource_types.py`.
- **Group ID:** a project-scoped prefix that avoids collisions with base game and other mods. Derived from `project_id` hash.
- **Instance ID:** derived from `(item_id, resource_kind[, swatch_index])` via stable hash.

If you need these values inside `dbpf_lib` (e.g. for testing), construct them via the functions in `sidecar/aisc/packaging/tgi.py`. Do not hardcode TGI values except in test fixtures.

## Testing

Critical tests live in `tests/dbpf_lib/`:

- `test_determinism.py` — identical inputs produce byte-identical output across multiple invocations
- `test_round_trip.py` — writing then reading yields the same resources with correct TGIs
- `test_header_integrity.py` — header fields match what the writer claimed
- `test_cross_platform_parity.py` — (run on both macOS and Windows CI) identical project state produces identical bytes on both platforms

Never commit changes to this package without running all four. Determinism is the single most important property of this code.

## Related Packages

- `sidecar/aisc/packaging/` — uses `dbpf_lib` to assemble full `.package` files from project state
- `sidecar/aisc/sims_install/` — uses `dbpf_lib` to read base-game `.package` files
- `sidecar/aisc/tuning/` — passes tuning XML through this package without modification

## Load These Docs When...

- Any DBPF work: `docs/tad/08-dbpf-packaging.md` is authoritative for design
- Understanding resource types: `docs/tad/08-dbpf-packaging.md` §10.3
- TGI ID generation: `docs/tad/08-dbpf-packaging.md` §10.2
- DDS encoding (used by callers, not this package): `docs/tad/08-dbpf-packaging.md` §10.4
- If D-1 is still unresolved: `docs/mvp/04-deferred-decisions.md`

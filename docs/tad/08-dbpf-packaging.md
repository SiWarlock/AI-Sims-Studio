# TAD — DBPF Packaging

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §10

> Library boundary, deterministic TGI ID generation, resource types produced, DDS encoding, catalog entry construction, custom filter tags.

---

## 10. DBPF Packaging

### 10.1 Library Boundary

All DBPF access is isolated behind the `dbpf_lib` module. This module exposes a stable interface:

```python
class DBPFWriter(Protocol):
    def open(self, path: str) -> None: ...
    def add_resource(self, tgi: TGI, data: bytes) -> None: ...
    def close(self) -> None: ...

class DBPFReader(Protocol):
    def open(self, path: str) -> None: ...
    def list_resources(self) -> list[TGI]: ...
    def read_resource(self, tgi: TGI) -> bytes: ...
    def close(self) -> None: ...
```

The underlying implementation (external library or custom, decided by D-1) is a detail of `dbpf_lib`.

### 10.2 TGI ID Generation

TGI (Type-Group-Instance) IDs are generated deterministically:

- **Type:** fixed per resource kind (mesh, diffuse texture, catalog entry, tuning, STBL)
- **Group:** a project-specific hash prefix (derived from project ID) to avoid collisions with base game and other mods
- **Instance:** derived from `item_id + resource_kind + swatch_index` as appropriate, via stable hash

This guarantees that the same project state produces the same TGI IDs on rebuild.

### 10.3 Resource Types Produced

Per decor item:

- Catalog entry (object definition)
- Mesh resource (low LOD + high LOD, if LODs are authored)
- Diffuse texture resources per zone, per swatch (DDS encoded)
- Normal texture resources per zone, per swatch
- Specular texture resources per zone, per swatch
- Thumbnail resource
- String table entries (name, description)

Per functional item (additive on top of decor):

- Object tuning XML
- Interaction tuning XML (if archetype adds/modifies interactions)
- Any broadcaster, state, or buff tuning needed by the archetype
- Additional string table entries for interaction names

### 10.4 DDS Encoding

Textures generated as PNG by the texture pipeline are encoded to DDS at packaging time:

- Diffuse with alpha: DXT5
- Diffuse without alpha: DXT1
- Normal: DXT5 (with tangent-space normal conventions)
- Specular: DXT1 or grayscale depending on channel content

The DDS encoder is a custom Python module built on `Pillow` + `numpy`, because cross-platform DDS libraries are inconsistent. Unit tests verify encoded output round-trips correctly.

### 10.5 Catalog Entry Construction

Catalog entries reference the object's mesh, textures (by swatch), thumbnail, and metadata (name, description, category, tags, price). Category assignment uses Sims 4's Build/Buy category taxonomy; the `ItemMetadata.build_buy_category` field is mapped to the correct internal category ID at packaging time.

### 10.6 Custom Catalog Filter Tags

When `ItemMetadata.custom_filter_tag` is set, a custom tag resource is added enabling the item to appear under a user-defined filter in Build/Buy. This uses the Sims 4 custom tag system (not custom category).

---

# Archetype Handlers — Claude Code Guidance

You are working inside `sidecar/aisc/archetypes/`. This package contains the four MVP archetype handlers: `light_on_off`, `audio_device`, `mirror`, `moodlet_emitter`.

Reminder: `sidecar/CLAUDE.md` and `CODING_STANDARDS.md` set the general rules. This file is the specialized one for archetype work.

## What An Archetype Handler Does

An archetype handler takes a decorative item (mesh + textures + metadata) and produces a functional variant by cloning the tuning from a specific base-game reference object and applying targeted edits based on user configuration.

Archetype handlers never generate tuning XML from scratch. They clone and modify. AI never touches the XML structure — AI only suggests configuration values, and deterministic code applies them to the cloned tuning.

## Handler Interface

Every archetype handler conforms to this protocol (defined in `sidecar/aisc/archetypes/base.py`):

```python
from typing import Protocol
from pydantic import BaseModel

class ArchetypeHandler(Protocol):
    archetype_id: ArchetypeId
    reference_object_lookup: ReferenceObjectLookup
    configuration_schema: type[BaseModel]
    compatible_templates: list[str]

    async def build_overlay(
        self,
        item: Item,
        template: Template,
        configuration: BaseModel,
        reference_resources: ReferenceResources,
    ) -> BuiltOverlay:
        ...

    def validate_configuration(
        self,
        configuration: BaseModel,
    ) -> list[ValidationIssue]:
        ...

    def summarize_behavior(self, configuration: BaseModel) -> str:
        ...
```

Every handler is a class (not just functions) that satisfies this Protocol.

## File Structure Per Archetype

```
archetypes/
├── __init__.py              # re-exports ARCHETYPE_REGISTRY
├── base.py                  # Protocol, base types, helpers
├── registry.py              # ARCHETYPE_REGISTRY: dict[ArchetypeId, ArchetypeHandler]
├── moodlet_catalog.py       # curated safe moodlet list
├── light_on_off.py
├── audio_device.py
├── mirror.py
└── moodlet_emitter.py
```

Each archetype file:

```python
# sidecar/aisc/archetypes/light_on_off.py
from pydantic import BaseModel, Field
from aisc.archetypes.base import BuiltOverlay, ArchetypeHandlerBase
from aisc.schemas.base import ArchetypeId

class LightOnOffConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    light_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    intensity: Literal["low", "medium", "high"] = "medium"
    always_on: bool = False

class LightOnOffHandler(ArchetypeHandlerBase):
    archetype_id = ArchetypeId.LIGHT_ON_OFF
    configuration_schema = LightOnOffConfig
    compatible_templates = [
        "cylindrical_small_tabletop",
        "cylindrical_tall_floor",
        "boxy_electronic_small_tabletop",
    ]

    async def build_overlay(self, item, template, configuration, reference_resources):
        # 1. Clone reference lamp tuning
        # 2. Locate editable fields (light color, intensity ref, state machine)
        # 3. Apply user's values
        # 4. Emit new tuning resources with fresh TGI IDs
        # 5. Return BuiltOverlay
        ...

    def validate_configuration(self, configuration: LightOnOffConfig):
        issues = []
        # archetype-specific validations beyond Pydantic
        return issues

    def summarize_behavior(self, configuration: LightOnOffConfig) -> str:
        color_name = color_hex_to_name(configuration.light_color)
        always = " (always on)" if configuration.always_on else ""
        return f"Emits {color_name} light at {configuration.intensity} intensity{always}."
```

## Hard Rules

1. **Configuration schemas are Pydantic v2 `frozen=True, extra="forbid"`.** Users can't pass unknown fields.
2. **Configuration validation happens at three levels:** Pydantic (type/format), `validate_configuration` (archetype-specific), and `build_overlay` (full context). The first two return `ValidationIssue`s; the third raises `AISCError` for hard failures.
3. **Editable tuning fields are documented per handler.** Each handler file includes a module-level docstring listing which tuning fields it modifies. This is the authoritative list — `build_overlay` must not touch fields outside this list.
4. **Never modify fields outside the declared list.** If a new capability is needed, extend the declared list, document it, and write a test for it.
5. **Every archetype has a dedicated test file** under `tests/archetypes/` that verifies: configuration validation, handler produces valid tuning, targeted edits don't break inherited fields, and the summary text is sensible.
6. **Handlers are stateless.** No instance state between calls. Tests construct a fresh handler per test.
7. **Reference resource access is read-only.** Handlers receive `ReferenceResources` (pre-extracted tuning, strings, meshes from the user's Sims install) and never modify them.

## Registry

All handlers register in `registry.py`:

```python
# sidecar/aisc/archetypes/registry.py
from aisc.archetypes.light_on_off import LightOnOffHandler
from aisc.archetypes.audio_device import AudioDeviceHandler
from aisc.archetypes.mirror import MirrorHandler
from aisc.archetypes.moodlet_emitter import MoodletEmitterHandler

ARCHETYPE_REGISTRY: dict[ArchetypeId, ArchetypeHandler] = {
    ArchetypeId.LIGHT_ON_OFF: LightOnOffHandler(),
    ArchetypeId.AUDIO_DEVICE: AudioDeviceHandler(),
    ArchetypeId.MIRROR: MirrorHandler(),
    ArchetypeId.MOODLET_EMITTER: MoodletEmitterHandler(),
}
```

Callers look up via the registry, not direct imports. This is how admin mode and the `functional.*` IPC namespace discover compatible archetypes for an item.

## Compatibility Check

Given a template ID, returning compatible archetypes:

```python
def compatible_archetypes_for_template(template_id: str) -> list[ArchetypeHandler]:
    return [
        h for h in ARCHETYPE_REGISTRY.values()
        if template_id in h.compatible_templates
    ]
```

The `functional.list_compatible_archetypes` IPC handler uses this. Do not duplicate this logic elsewhere.

## Moodlet Catalog

`moodlet_emitter` uses a curated list of safe base-game moodlets to prevent users from attaching anything that could break saves or cause weird gameplay interactions. The catalog lives in `moodlet_catalog.py`:

```python
# sidecar/aisc/archetypes/moodlet_catalog.py
SAFE_MOODLETS = [
    MoodletEntry(id="focused", display_name="Focused", ...),
    MoodletEntry(id="inspired", display_name="Inspired", ...),
    # ...
]
```

The exact list is locked during Phase 5 (see `docs/mvp/10-phase-5-functional.md`). Do not add moodlets without updating the tests and confirming they don't have surprising in-game effects.

## Load These Docs When...

- Adding a new archetype or modifying an existing one: `docs/tad/06-archetype-handlers.md` + `docs/mvp/03-archetype-mapping.md`
- Understanding tuning: `docs/tad/09-tuning-clone.md` and `sidecar/aisc/tuning/` module
- DBPF resource packaging: `docs/tad/08-dbpf-packaging.md` + `sidecar/aisc/dbpf_lib/CLAUDE.md`
- IPC for archetype work: `docs/api/07-functional.md`
- Phase 5 task breakdown: `docs/mvp/10-phase-5-functional.md`

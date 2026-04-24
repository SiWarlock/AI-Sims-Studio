# Sidecar — Claude Code Guidance

You are working inside `sidecar/`. This is the Python 3.12 sidecar: a single long-running asyncio process that owns all generation logic, AI integrations, file operations, DBPF packaging, tuning cloning, and project persistence.

The frontend never calls external APIs or the file system directly. Everything that leaves the machine, every subprocess, every Blender invocation goes through code in this directory.

Reminder: `CODING_STANDARDS.md` at the repo root has the full Python style and quality rules. This file covers patterns specific to sidecar work.

## Layout

```
sidecar/
├── aisc/                    # package root
│   ├── __init__.py
│   ├── main.py              # entry point, stdio JSON-RPC server
│   ├── ipc/                 # JSON-RPC protocol + typed handlers
│   │   ├── server.py        # stdio server
│   │   ├── handlers/        # one file per namespace (project, item, export, etc.)
│   │   └── notify.py        # push notification helpers
│   ├── config/              # paths, platform detection, feature flags
│   ├── storage/             # SQLite access + project CRUD
│   ├── schemas/             # Pydantic models (shared with frontend via codegen)
│   ├── planning/            # Claude-backed collection planning
│   ├── spec_gen/            # Claude-backed per-item spec generation
│   ├── texture_gen/         # Replicate texture generation pipeline
│   ├── thumbnail/           # Blender subprocess wrapper
│   ├── assembly/            # mesh + texture → render-ready asset
│   ├── dbpf_lib/            # DBPF library adapter (see its own CLAUDE.md)
│   ├── packaging/           # DBPF assembly for decor and functional
│   ├── tuning/              # tuning parsing, cloning, targeted edits
│   ├── archetypes/          # archetype handlers (see its own CLAUDE.md)
│   ├── validation/          # validation engine
│   ├── install/             # Mods folder auto-install
│   ├── templates/           # template registry (see its own CLAUDE.md)
│   ├── sims_install/        # read-only base-game resource extraction
│   ├── admin/               # admin mode operations
│   ├── jobs/                # async job scheduler, progress events
│   ├── logging_setup/       # structlog configuration
│   └── errors/              # error taxonomy, AISCError subclasses
├── tests/                   # pytest tree mirroring aisc/
├── migrations/              # yoyo-migrations for SQLite schema
├── scripts/                 # blender scripts invoked via subprocess
└── pyproject.toml
```

## Process Model

- **Single persistent process.** Launched by Tauri at app start, shuts down cleanly at app exit.
- **asyncio event loop** hosts the JSON-RPC server (stdio) and the job scheduler.
- **Long-running jobs are asyncio tasks** in the same loop.
- **Blocking work** (Blender subprocess, DBPF writes, large image encoding) runs in `loop.run_in_executor(None, ...)` to avoid blocking the event loop.
- **Graceful shutdown:** `system.shutdown` request triggers a clean shutdown — in-flight jobs cancel, state persists, process exits.

## IPC Handler Pattern

Every IPC method has a handler in `sidecar/aisc/ipc/handlers/{namespace}.py`.

Shape:

```python
# sidecar/aisc/ipc/handlers/project.py
from aisc.schemas.project import Project, ProjectCreateParams, ProjectCreateResult
from aisc.storage import project_store
from aisc.errors import AISCError, ProjectNotFoundError

async def project_create(params: ProjectCreateParams) -> ProjectCreateResult:
    """Handler for project.create IPC method."""
    # 1. Validate params (Pydantic did it already via the handler dispatcher)
    # 2. Execute (delegate to storage/service layer)
    project = await project_store.create(
        name=params.name,
        theme_prompt=params.theme_prompt,
        mode=params.mode,
        target_item_count=params.target_item_count,
        style_preference=params.style_preference,
    )
    # 3. Return typed result
    return ProjectCreateResult(
        project_id=project.id,
        collection_id=project.default_collection_id,
        created_at=project.created_at,
    )
```

Rules:

- **Handler function name matches the IPC method** with dots replaced by underscores (`project.create` → `project_create`).
- **Handlers are thin orchestration.** Business logic lives in `storage/`, `planning/`, `packaging/`, etc. Handlers validate → dispatch → format response.
- **Never catch all exceptions.** Let `AISCError` subclasses propagate to the IPC layer, which formats them into JSON-RPC errors. Catch only the specific exceptions you can meaningfully handle.

## Schema Conventions

All schemas live in `sidecar/aisc/schemas/`. Organize by domain:

```
schemas/
├── __init__.py              # re-exports
├── base.py                  # base types, common enums
├── project.py               # Project, ProjectCreate*, ProjectOpen*
├── collection.py
├── item.py
├── swatch.py
├── functional.py
├── template.py
├── validation.py
├── export.py
├── jobs.py
└── errors.py                # error data shapes (not AISCError classes)
```

Each schema file:

```python
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class Project(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    theme_prompt: str
    # ...
    schema_version: int = 1
```

When you add or change a schema:

1. Edit the schema file.
2. Run `python scripts/generate_types.py` (or it will run automatically via post-edit hook).
3. The TypeScript equivalent appears in `shared-types/`.
4. The post-edit hook fails the commit if regeneration produces a diff that wasn't staged. This prevents drift.

## Storage Layer

All persistence uses SQLite + file tree under the project folder. No SQLAlchemy. Direct `sqlite3` with thin typed wrappers.

```python
# sidecar/aisc/storage/project_store.py
async def create(name: str, theme_prompt: str, ...) -> Project:
    project_id = uuid4()
    async with project_db.transaction(project_id) as db:
        await db.execute(
            "INSERT INTO projects (id, name, theme_prompt, ...) VALUES (?, ?, ?, ...)",
            (str(project_id), name, theme_prompt, ...),
        )
        # return hydrated Project model
```

Rules:

- **Every store function returns a Pydantic model**, not a dict or tuple.
- **Foreign key enforcement is on.** SQLite's `PRAGMA foreign_keys = ON` at connection creation.
- **Transactions via an async context manager.** Never raw `connection.commit()`.
- **Migrations via `yoyo-migrations`** in `sidecar/migrations/`. Apply on startup when project's `schema_version` lags.

## AI Client Wrappers

External clients (Anthropic, Replicate) are wrapped in thin adapters under `sidecar/aisc/{planning,spec_gen,texture_gen}/`. Every adapter:

- Enforces the request schema
- Enforces the response schema
- Logs prompt, model, latency, token counts, estimated cost
- Implements the retry policy (see `docs/tad/05-ai-orchestration.md`)
- Surfaces structured errors via `AISCError` subclasses

Never call the Anthropic SDK or Replicate SDK from anywhere except these adapter modules. Tests mock them at the adapter boundary.

## Blender Invocation

Blender runs as a subprocess invoked from `sidecar/aisc/thumbnail/`:

```python
import asyncio
from pathlib import Path

async def render_thumbnail(job_spec_path: Path, out_path: Path) -> None:
    proc = await asyncio.create_subprocess_exec(
        blender_path,
        "--background",
        "--python", str(render_script_path),
        "--",
        str(job_spec_path),
        str(out_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise BlenderSubprocessError(
            message_admin=f"Blender exited with {proc.returncode}. stderr: {stderr!r}",
            message_user="The thumbnail renderer failed. Try regenerating.",
        )
```

Rules:

- **Use `asyncio.create_subprocess_exec`**, not `subprocess.run`.
- **Always capture stderr.** It's the primary debugging signal for Blender failures.
- **Never run Blender on the event loop thread.** It's a subprocess, not a library call.
- **Thumbnail rendering is serial for MVP.** One Blender subprocess at a time.

## Progress Notifications

Pipeline stages push progress events via `aisc.ipc.notify`:

```python
from aisc.ipc.notify import notify

async def generate_textures(item_id: UUID, ...) -> TextureSet:
    # ... work ...
    await notify(
        method="generation.progress",
        params={
            "job_id": str(job_id),
            "stage": "texture_gen",
            "target_entity_type": "Swatch",
            "target_entity_id": str(swatch_id),
            "progress_ratio": 0.5,
            "message_user": "Generating textures (2 of 3 zones)...",
        },
    )
```

## Testing

- **pytest + pytest-asyncio + pytest-mock.**
- **`tests/` mirrors `aisc/` structure.** `aisc/storage/project_store.py` → `tests/storage/test_project_store.py`.
- **Fixtures in `tests/fixtures/`:** sample projects, mocked AI responses, synthetic DBPF files.
- **Every new module gets unit tests in the same PR.**
- **External deps are mocked.** No real API calls, no real Blender, no real Sims install reads in unit tests.
- **Integration tests have the `@pytest.mark.integration` decorator** and may assume mocked external clients but real storage + real DBPF.

## Load These Docs When...

- Adding a new Pydantic model: `docs/tad/02-data-model.md`
- Adding a new IPC method: the `docs/api/{namespace}.md` shard for that namespace + `docs/tad/03-ipc-architecture.md`
- Adding a pipeline stage: `docs/tad/04-pipelines.md`
- Adding an AI call: `docs/tad/05-ai-orchestration.md`
- DBPF or tuning work: `docs/tad/08-dbpf-packaging.md` + `docs/tad/09-tuning-clone.md` + the subdirectory CLAUDE.md for those packages
- Error handling: `docs/tad/14-errors-logging.md`
- Testing strategy: `docs/mvp/14-testing-strategy.md`

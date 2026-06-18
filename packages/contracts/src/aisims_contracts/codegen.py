"""§4 py→ts codegen + CI drift gate.

The pydantic models are the single source. build_combined_schema() aggregates all 7 contracts'
public models (via pydantic.json_schema.models_json_schema, which dedupes the shared $defs — enums +
embedded models), normalizes field schemas (Q6), and emits a deterministic combined JSON Schema.
generate() writes that schema + runs json-schema-to-typescript (Node) to emit generated/contracts.ts
plus a parseErrorCode tolerance helper (generated/helpers.ts) and the §4 IPC endpoint/protocol
catalog (generated/ipc-catalog.ts, ledger T3 — pure-Python, no node, mirrors ipc.py's catalog).

check() is the drift gate: regenerate to a temp dir, diff committed generated/ (exit non-zero on any
difference). The SCHEMA half (schema_matches) is pure Python — the primary, always-runnable
cross-track enforcement that a model change without a regen fails the gate; the TS half needs Node.
Determinism (a fixed banner, sorted keys, no timestamps) is required or the gate false-positives.
Build-time tooling — the aggregator imports all 7 contracts (top of the intra-package DAG); NOT
a §2.5 seam, so it is exempt from the per-module import-direction guards.
"""

import inspect
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from aisims_contracts import domain, error, ipc, providers, registries, responses, workers
from aisims_contracts.error import ErrorCode

# Repo paths (this file: packages/contracts/src/aisims_contracts/codegen.py).
_CONTRACTS_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = _CONTRACTS_ROOT / "generated"
_EMIT_SCRIPT = _CONTRACTS_ROOT / "scripts" / "emit-ts.mjs"

# Every frozen contract, in stable order (the aggregator picks up new public models per module).
_CONTRACT_MODULES: list[ModuleType] = [
    error,
    domain,
    ipc,
    responses,
    providers,
    workers,
    registries,
]


def _models_in(module: ModuleType) -> list[type[BaseModel]]:
    """Every public pydantic model DEFINED in the module (not imported; private _ bases excluded),
    name-sorted for determinism. Enums + embedded models ride in via $defs automatically.

    Assumes each contract is its own submodule (matched by ``__module__``); a model defined directly
    in the package ``__init__`` would not be picked up — contracts live in their own modules."""
    return sorted(
        (
            obj
            for name, obj in vars(module).items()
            if inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj.__module__ == module.__name__
            and not name.startswith("_")
        ),
        key=lambda model: model.__name__,
    )


ALL_CONTRACT_MODELS: list[type[BaseModel]] = [
    model for module in _CONTRACT_MODULES for model in _models_in(module)
]


def _normalize_field_schemas(defs: dict[str, Any]) -> None:
    """Make ref-typed fields emit clean TS:

    - Q6: drop the noisy pydantic per-field auto-titles (creatorMessage → 'Creatormessage') so the
      generated JSDoc reads from the field name (model-level titles, the type names, are kept).
    - Collapse a $ref that carries sibling keys (a defaulted enum field emits
      {"$ref": …, "default": …}) to a bare $ref — otherwise json-schema-to-typescript mints a
      duplicate Foo1 type for the defaulted variant. TS types don't encode defaults, and the
      per-module freeze snapshots (which keep the defaults) are untouched.
    """
    for model_schema in defs.values():
        properties = model_schema.get("properties")
        if not isinstance(properties, dict):
            continue
        for field_schema in properties.values():
            if not isinstance(field_schema, dict):
                continue
            field_schema.pop("title", None)
            # A defaulted enum/model field emits {"$ref": …, "default": …}; that sibling makes
            # json-schema-to-typescript mint a duplicate Foo1. Drop ONLY the default (any other
            # sibling, e.g. a description, is preserved). The freeze snapshots keep the default.
            if "$ref" in field_schema:
                field_schema.pop("default", None)
            # An allOf wrapping a single bare $ref (with at most a default) → collapse to the $ref;
            # the membership guards keep this from clobbering a field with meaningful siblings.
            elif (
                set(field_schema) <= {"allOf", "default"}
                and isinstance(field_schema.get("allOf"), list)
                and len(field_schema["allOf"]) == 1
                and isinstance(field_schema["allOf"][0], dict)
                and set(field_schema["allOf"][0]) == {"$ref"}
            ):
                ref = field_schema["allOf"][0]["$ref"]
                field_schema.clear()
                field_schema["$ref"] = ref


def build_combined_schema() -> dict[str, Any]:
    """The single combined JSON Schema for all frozen contracts (single source = pydantic).

    Deterministic: ``$defs`` sorted by name; field titles stripped; no timestamps."""
    _, combined = models_json_schema(
        [(model, "validation") for model in ALL_CONTRACT_MODELS],
        ref_template="#/$defs/{model}",
    )
    defs = combined.get("$defs", {})
    _normalize_field_schemas(defs)
    return {"$defs": dict(sorted(defs.items()))}


def build_helpers_ts() -> str:
    """The ErrorCode tolerance helper (carry-forward 0.2/D10b): a strict closed producer enum +
    a tolerant consumer that degrades an unrecognized code to SYSTEM (so a future additive enum
    split is non-breaking). 0.6 ships the primitive; UI Zod-boundary wiring is Phase 7."""
    known = ", ".join(f"'{code.value}'" for code in sorted(ErrorCode, key=lambda c: c.value))
    return (
        "/* eslint-disable */\n"
        "/* AUTO-GENERATED by aisims_contracts.codegen — DO NOT EDIT. */\n"
        "import type { ErrorCode } from './contracts';\n\n"
        f"const KNOWN_ERROR_CODES: ReadonlySet<string> = new Set([{known}]);\n\n"
        "/**\n"
        " * Strict producer / tolerant consumer (carry-forward 0.2/D10b): an unknown code\n"
        " * degrades to SYSTEM so a future additive enum split stays non-breaking. The producer\n"
        " * remains a strict closed enum; this tolerance lives in the consumer. UI Zod-boundary\n"
        " * wiring is Phase 7 (the carry-forward's other last-consumer).\n"
        " */\n"
        "export function parseErrorCode(value: string): ErrorCode {\n"
        "  return (KNOWN_ERROR_CODES.has(value) ? value : 'SYSTEM') as ErrorCode;\n"
        "}\n"
    )


def build_ipc_catalog_ts() -> str:
    """The §4 IPC protocol/endpoint catalog (ledger T3): the endpoint ``METHOD path`` values, the
    mutating / read-only partition, the token + idempotency header names, and the contractVersion —
    emitted to a deterministic TS module so the UI imports it instead of the hand-authored,
    drift-guarded ``endpoints.ts``. Pure-Python (no node), like ``build_helpers_ts``; the committed
    artifact is diffed by ``check()``; ``test_codegen_emits_ipc_catalog`` pins it (no-node half).

    Determinism: endpoint lists are value-sorted (by ``METHOD path``), header/version come from
    ``ipc``, a fixed banner, no timestamps — required or the drift gate false-positives (§4)."""
    endpoints = sorted(endpoint.value for endpoint in ipc.Endpoint)
    mutating = sorted(endpoint.value for endpoint in ipc.MUTATING_ENDPOINTS)
    read_only = sorted(endpoint.value for endpoint in ipc.READ_ONLY_ENDPOINTS)

    def _members(values: list[str]) -> str:
        return "".join(f"  '{value}',\n" for value in values)

    return (
        "/* eslint-disable */\n"
        "/* AUTO-GENERATED by aisims_contracts.codegen — DO NOT EDIT. */\n\n"
        f"export const CONTRACT_VERSION = '{ipc.CONTRACT_VERSION}';\n"
        f"export const TOKEN_HEADER = '{ipc.TOKEN_HEADER}';\n"
        f"export const IDEMPOTENCY_KEY_HEADER = '{ipc.IDEMPOTENCY_KEY_HEADER}';\n\n"
        "/** Every §4 REST endpoint as its `METHOD path` value (sorted). */\n"
        f"export const ENDPOINTS = [\n{_members(endpoints)}] as const;\n"
        "export type Endpoint = (typeof ENDPOINTS)[number];\n\n"
        "/** Mutating endpoints — an Idempotency-Key is required (R9). */\n"
        "export const MUTATING_ENDPOINTS: ReadonlySet<Endpoint> = "
        f"new Set<Endpoint>([\n{_members(mutating)}]);\n\n"
        "/** Pure-read endpoints — no Idempotency-Key. */\n"
        "export const READ_ONLY_ENDPOINTS: ReadonlySet<Endpoint> = "
        f"new Set<Endpoint>([\n{_members(read_only)}]);\n"
    )


def schema_matches(committed_schema_path: Path) -> bool:
    """Pure-Python schema-level drift check: the committed combined schema == the current pydantic
    source. The primary, always-runnable gate half (a model change without a regen fails here)."""
    if not committed_schema_path.exists():
        return False
    committed = json.loads(committed_schema_path.read_text())
    return bool(build_combined_schema() == committed)


def _write_schema(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    schema_path = out_dir / "contracts.schema.json"
    schema_path.write_text(json.dumps(build_combined_schema(), indent=2, sort_keys=True) + "\n")
    return schema_path


def _emit_typescript(schema_path: Path, ts_path: Path) -> None:
    """Run the Node json-schema-to-typescript emitter (the py→ts boundary)."""
    subprocess.run(
        ["node", str(_EMIT_SCRIPT), str(schema_path), str(ts_path)],
        check=True,
        cwd=_CONTRACTS_ROOT,
    )


def generate(out_dir: Path) -> None:
    """Write the full generated tree: contracts.schema.json + contracts.ts + helpers.ts +
    ipc-catalog.ts (the §4 endpoint/protocol catalog, ledger T3)."""
    schema_path = _write_schema(out_dir)
    _emit_typescript(schema_path, out_dir / "contracts.ts")
    (out_dir / "helpers.ts").write_text(build_helpers_ts())
    (out_dir / "ipc-catalog.ts").write_text(build_ipc_catalog_ts())


def check() -> bool:
    """Drift gate: regenerate to a temp dir, diff every committed generated/ artifact (schema + TS +
    helpers + ipc-catalog). True = clean. Needs Node (the TS half); ``schema_matches`` is the
    pure-Python schema half, ``build_ipc_catalog_ts`` the pure-Python catalog half."""
    with tempfile.TemporaryDirectory() as tmp:
        generate(Path(tmp))
        for name in ("contracts.schema.json", "contracts.ts", "helpers.ts", "ipc-catalog.ts"):
            committed = GENERATED_DIR / name
            fresh = Path(tmp) / name
            if not committed.exists() or committed.read_text() != fresh.read_text():
                return False
    return True


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    # Both paths shell out to the Node emitter — guard once with a clean message (no stack trace).
    if shutil.which("node") is None:
        print("node not found — required for the TS emitter / drift gate.", file=sys.stderr)
        return 2
    if "--check" in args:
        if check():
            return 0
        print(
            "DRIFT: generated/ is out of sync with the pydantic source. "
            "Run `python -m aisims_contracts.codegen`.",
            file=sys.stderr,
        )
        return 1
    generate(GENERATED_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

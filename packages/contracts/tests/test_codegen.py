"""RED tests for the §4 py→ts codegen + CI drift gate — slice 0.6.

The pydantic models are the single source → a combined JSON Schema (the codegen aggregates every
frozen contract via ``pydantic.json_schema.models_json_schema``) → generated TypeScript (emitted by
``json-schema-to-typescript``). A ``--check`` drift gate regenerates and diffs against the committed
``generated/`` tree so a model change without a regen fails CI.

Covers the Python core (combined-schema build + determinism + the schema-level drift gate) plus the
node-coupled TS-emission tests (skipif when node / the emitter is unavailable).
"""

import json
import shutil
from pathlib import Path

import pytest

from aisims_contracts import codegen
from aisims_contracts.error import ErrorCode

_NODE_DEP = (Path(__file__).parent.parent / "node_modules" / "json-schema-to-typescript").exists()
requires_node = pytest.mark.skipif(
    not (shutil.which("node") and _NODE_DEP),
    reason="node + json-schema-to-typescript (pnpm install --ignore-workspace) required",
)

GENERATED_DIR = Path(__file__).parent.parent / "generated"
SCHEMA_PATH = GENERATED_DIR / "contracts.schema.json"

# One representative model per frozen contract that MUST land in the combined schema's $defs.
EXPECTED_DEFS = {
    "ErrorEnvelope",
    "ErrorCode",  # error
    "ProgressEvent",
    "DoneEvent",  # ipc (SSE union)
    "CreateProjectResponse",  # responses
    "Project",
    "AssetVariant",  # domain
    "ProviderJobRef",
    "PollStatus",  # providers
    "BlenderReport",
    "ExportJobReport",  # workers
    "PlacementType",
    "RegistryFinding",  # registries
}


def test_build_combined_schema_covers_all_contracts() -> None:  # spec(§4)
    """The combined schema (single source = pydantic) carries every frozen contract's models."""
    schema = codegen.build_combined_schema()
    defs = set(schema.get("$defs", {}))
    assert EXPECTED_DEFS <= defs, f"combined schema missing: {EXPECTED_DEFS - defs}"


def test_codegen_deterministic() -> None:  # spec(§4)
    """Stable ordering + no timestamps → byte-identical across runs (reproducible gate)."""
    a = json.dumps(codegen.build_combined_schema(), indent=2, sort_keys=True)
    b = json.dumps(codegen.build_combined_schema(), indent=2, sort_keys=True)
    assert a == b


def test_field_titles_stripped() -> None:  # spec(§4)
    """Q6: noisy pydantic auto-titles (creatorMessage → 'Creatormessage') are stripped by codegen
    so the JSDoc reads from the field name — without re-freezing the 7 snapshots."""
    env = codegen.build_combined_schema()["$defs"]["ErrorEnvelope"]["properties"]
    assert "title" not in env["creatorMessage"]


def test_drift_gate_passes_clean() -> None:  # spec(§4)
    """The committed generated schema matches the current pydantic source (no false positives)."""
    assert SCHEMA_PATH.exists(), "generated/contracts.schema.json must be committed"
    assert codegen.schema_matches(SCHEMA_PATH) is True


def test_drift_gate_fails_on_drift(tmp_path: Path) -> None:  # spec(§4)
    """A stale/tampered committed schema (a model change without a regen) fails the gate."""
    if not SCHEMA_PATH.exists():
        pytest.skip("generated/contracts.schema.json not present")
    tampered = json.loads(SCHEMA_PATH.read_text())
    tampered["$defs"].pop(next(iter(tampered["$defs"])))  # drop a def → simulated drift
    tampered_path = tmp_path / "contracts.schema.json"
    tampered_path.write_text(json.dumps(tampered))
    assert codegen.schema_matches(tampered_path) is False


def test_errorcode_tolerance() -> None:  # spec(§4)
    """Carry-forward 0.2/D10b: the generated ErrorCode consumer degrades an unknown code → SYSTEM
    (strict producer / tolerant consumer), so a future additive enum split is non-breaking."""
    helpers = codegen.build_helpers_ts()
    assert "export function parseErrorCode(value: string): ErrorCode" in helpers
    assert "'SYSTEM'" in helpers  # the fallback for an unrecognized code
    # every known code is in the recognized set (the producer stays a strict closed enum).
    for code in ErrorCode:
        assert f"'{code.value}'" in helpers


@requires_node
def test_codegen_emits_ts(tmp_path: Path) -> None:  # spec(§4)
    """The full chain emits TypeScript for every frozen contract (importable by the UI / worker)."""
    codegen.generate(tmp_path)
    ts = (tmp_path / "contracts.ts").read_text()
    for ty in ("ErrorEnvelope", "PollStatus", "BlenderReport", "ProviderJobRef", "RegistryFinding"):
        assert f"{ty}" in ts, ty
    # no duplicate-suffixed types (a defaulted-enum field must not mint `Foo1`).
    import re

    assert not re.search(r"export type [A-Za-z]+[0-9] =", ts)


@requires_node
def test_drift_gate_ts_passes_clean() -> None:  # spec(§4)
    """The committed generated tree (schema + TS + helpers) matches a fresh regen (full gate)."""
    assert codegen.check() is True

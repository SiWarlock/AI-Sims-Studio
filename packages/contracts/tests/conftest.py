"""Shared pytest fixtures for the contracts test suite."""

import ast
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

IntraImports = Callable[[ModuleType], set[str]]


def _intra_imports(module: ModuleType) -> set[str]:
    """The set of sibling ``aisims_contracts`` submodules imported by ``module`` (parsed from its
    source AST — robust to imports appearing in comments/strings).

    The shared engine behind every per-module import-direction guard (test_responses,
    test_providers, + the 0.5b/0.5c siblings) that pins the acyclic intra-package DAG
    ``error ← domain ← {ipc, providers} ← responses``. Do NOT call on the package ``__init__`` — it
    re-exports from all siblings, so its result would look like cycles and mislead a debug session.
    """
    tree = ast.parse(Path(module.__file__ or "").read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("aisims_contracts.")
        ):
            imported.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("aisims_contracts."):
                    imported.add(alias.name.split(".")[1])
    return imported


@pytest.fixture
def intra_imports() -> IntraImports:
    """Inject ``_intra_imports`` into the per-module import-direction guards."""
    return _intra_imports

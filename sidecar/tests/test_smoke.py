"""Smoke tests to confirm the sidecar package imports and the test runner works."""

from __future__ import annotations

import importlib

import aisc


def test_package_version_exists() -> None:
    assert isinstance(aisc.__version__, str)


def test_subpackages_import() -> None:
    """Every declared sidecar subpackage should be importable without error."""
    for name in (
        "aisc.ipc",
        "aisc.config",
        "aisc.storage",
        "aisc.schemas",
        "aisc.planning",
        "aisc.spec_gen",
        "aisc.texture_gen",
        "aisc.thumbnail",
        "aisc.assembly",
        "aisc.packaging",
        "aisc.tuning",
        "aisc.validation",
        "aisc.install",
        "aisc.sims_install",
        "aisc.admin",
        "aisc.jobs",
        "aisc.logging_setup",
        "aisc.errors",
        "aisc.archetypes",
        "aisc.dbpf_lib",
        "aisc.templates",
    ):
        importlib.import_module(name)

"""Smoke test for the integration runner.

Phase 0 bootstrap: this file exists only so that `pytest -q -m integration`
collects at least one test and exits successfully. Real integration tests
(hitting SQLite, DBPF packaging, etc.) land from Task 0.5 onward.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_integration_runner_collects_at_least_one_test() -> None:
    assert True

"""Mock adapter framework (§7/§8/§9 + §17 failure injection) — Phase-0 test infra.

The provider mocks + the deterministic failure-injection core live in ``providers`` / ``failure``;
the worker mocks and the package-level factory seam (``MOCK_PROVIDERS`` / ``MOCK_WORKERS``) land
alongside ``workers``.
"""

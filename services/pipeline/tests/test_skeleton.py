"""Phase-0 scaffold smoke test for the pipeline sidecar.

Confirms the §2.5 subsystem package skeleton imports cleanly. Real stage/engine/adapter
tests land in Phase 2 (graph · engine · reconciler · store).
"""


def test_pipeline_subsystem_packages_importable() -> None:
    import adapters
    import engine
    import graph
    import obs
    import registries
    import store

    for pkg in (graph, engine, adapters, registries, store, obs):
        assert pkg.__name__

"""Shared C1/C2 test infra for the imagegen adapter: a header-scrubbing cassette context + a
SecretsAccessor spy.

Same cassette posture as the 3.3 LLM tests (vcr, replay-only by default, auth headers filtered);
``AISIMS_IMAGEGEN_RECORD`` flips the record mode for refreshing cassettes from the live smoke. The
adapter's request-body construction is unit-tested via the pure ``build_submit_body`` helper (vcr
matches on method+uri, not body, so the cassette can't pin outgoing-body content).
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path

import pytest

from obs.secrets import SecretsAccessor

CASSETTE_DIR = Path(__file__).parent / "cassettes"
SCRUB_HEADERS = ["authorization", "x-api-key", "api-key"]


class SpyAccessor:
    """A SecretsAccessor that records every get() so a test can prove the key is pulled through
    the accessor seam at call time (never stashed on the adapter). Conforms to the Protocol."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = dict(secrets)
        self.get_calls: list[str] = []

    def get(self, name: str) -> str | None:
        self.get_calls.append(name)
        return self._secrets.get(name)

    def active_values(self) -> tuple[str, ...]:
        return tuple(self._secrets.values())

    def __repr__(self) -> str:
        return f"SpyAccessor(names={sorted(self._secrets)!r})"  # names only, never values


def _assert_accessor(_: SecretsAccessor) -> None:
    """Static guard: SpyAccessor structurally satisfies SecretsAccessor (mypy --strict)."""


_assert_accessor(SpyAccessor({}))


@pytest.fixture
def imagegen_cassette() -> Callable[[str], AbstractContextManager[None]]:
    """Replay the named committed cassette (auth headers scrubbed). Replay-only (record_mode='none')
    unless AISIMS_IMAGEGEN_RECORD overrides it."""

    @contextmanager
    def _use(name: str) -> Iterator[None]:
        import vcr  # type: ignore[import-untyped]  # test-only dep, ships no py.typed

        my_vcr = vcr.VCR(
            record_mode=os.environ.get("AISIMS_IMAGEGEN_RECORD", "none"),
            filter_headers=SCRUB_HEADERS,
        )
        with my_vcr.use_cassette(str(CASSETTE_DIR / f"{name}.yaml")):
            yield

    return _use

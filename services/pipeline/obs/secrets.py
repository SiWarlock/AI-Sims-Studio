"""§16 single secrets accessor (forbidden-pattern 5).

The ONE place secrets are read. Values are returned at point of use and NEVER leaked into a
repr/str surface that could land in a log or trace. Phase-0 skeleton (in-memory / injected for
tests); the real OS-keychain integration is Phase-7 onboarding. The redactor consults
``active_values()`` at egress time to scrub any live secret.
"""

from __future__ import annotations

from typing import Protocol


class SecretsAccessor(Protocol):
    def get(self, name: str) -> str | None: ...

    def active_values(self) -> tuple[str, ...]: ...


class InMemorySecretsAccessor:
    """Phase-0 in-memory secrets accessor — never persists/leaks values into a loggable surface."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = dict(secrets)

    def get(self, name: str) -> str | None:
        return self._secrets.get(name)

    def active_values(self) -> tuple[str, ...]:
        return tuple(self._secrets.values())

    def __repr__(self) -> str:
        # names only — NEVER the values (this repr can land in a log/trace)
        return f"InMemorySecretsAccessor(names={sorted(self._secrets)!r})"

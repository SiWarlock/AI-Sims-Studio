"""§18/§16/§13 sidecar keychain READ accessor (forbidden-pattern 5).

The sidecar-side ``SecretsAccessor`` (the structural Protocol in ``obs/secrets.py``) that reads
provider API keys from the OS keychain via ``keyring`` at the ui-owned named entry
(``service="AISimsCreator"``, ``account=<providerId>``) — the SAME entry ``apps/desktop`` writes
(7.2b-1; interop proven by spike 7.2b-0). A structural drop-in for the §16 redactor, which
consults ``active_values()`` at egress to scrub any live secret.

Values are read at point of use and NEVER leak into a repr/str/exception/log surface (rule 5).
The ``keyring`` backend is injected so unit tests touch no real keychain; boot-time selection
(swap ``InMemorySecretsAccessor`` → this accessor) is a Phase-2 supervisor TODO, not this slice.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import keyring
from keyring.errors import KeyringError

# Cross-process secret-name contract with the UI writer
# (apps/desktop/electron/keychain.ts:KEYCHAIN_SERVICE). Must stay byte-identical both ends — the
# spike (7.2b-0) proved the Node-writer / Python-reader round-trip on this exact service name.
KEYCHAIN_SERVICE = "AISimsCreator"

GetPassword = Callable[[str, str], str | None]


class KeychainUnavailableError(RuntimeError):
    """The OS keychain backend is unavailable/locked/denied — distinct from a legitimately-absent
    key (which is ``None``). Carries the provider NAME only: never a secret value, and never the
    raw keyring cause (rule 5 — an underlying backend message may name internals)."""

    def __init__(self, provider_id: str) -> None:
        super().__init__(f"keychain unavailable for provider {provider_id!r}")


class KeychainSecretsAccessor:
    """Reads provider keys from the OS keychain at (service="AISimsCreator", account=providerId).

    A structural ``SecretsAccessor`` (``obs/secrets.py``) — drop-in for the §16 redactor.
    Constructed with the set of active provider ids (``keyring`` has no portable enumeration;
    Phase-2 supplies the real configured list) and an injectable ``get_password`` backend
    (production default = ``keyring.get_password``; tests inject a fake — no real keychain).
    """

    def __init__(
        self,
        provider_ids: Iterable[str],
        *,
        get_password: GetPassword = keyring.get_password,
    ) -> None:
        # The configured set is conceptually unique — dedup, preserving first-seen order, so a
        # duplicate id never causes a double keychain read or a double value in active_values().
        self._provider_ids: tuple[str, ...] = tuple(dict.fromkeys(provider_ids))
        self._get_password = get_password

    def get(self, name: str) -> str | None:
        """Read one provider's key. Absent → ``None`` (no raise). A locked/unavailable backend
        (``KeyringError``, incl. macOS ``KeyringLocked``) → a fresh ``KeychainUnavailableError``
        (name only, ``from None`` — no raw cause leaks)."""
        try:
            return self._get_password(KEYCHAIN_SERVICE, name)
        except KeyringError:
            raise KeychainUnavailableError(name) from None

    def active_values(self) -> tuple[str, ...]:
        """The live secret values for the §16 redactor's egress scrub, in configured
        provider order. FAIL-SAFE: a per-provider read that raises is SKIPPED (never propagated) so
        the redactor always gets a tuple and keeps functioning; absent (``None``) keys are skipped
        too. An unreadable key never entered the process, so there is nothing to scrub."""
        values: list[str] = []
        for provider_id in self._provider_ids:
            try:
                value = self._get_password(KEYCHAIN_SERVICE, provider_id)
            except KeyringError:
                continue
            if value is not None:
                values.append(value)
        return tuple(values)

    def __repr__(self) -> str:
        # provider NAMES only — NEVER the values (this repr can land in a log/trace).
        return f"KeychainSecretsAccessor(providers={sorted(self._provider_ids)!r})"

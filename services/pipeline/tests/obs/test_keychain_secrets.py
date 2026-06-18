"""RED — [SAFETY · RULE 5] §18/§16/§13 sidecar keychain READ accessor.

The sidecar-side ``SecretsAccessor`` reads provider API keys from the OS keychain via ``keyring``
at the ui-owned named entry (``service="AISimsCreator"``, ``account=<providerId>``) — the SAME
entry ``apps/desktop`` writes (7.2b-1; interop proven by spike 7.2b-0). It is a structural drop-in
for the §16 redactor (which consults ``active_values()`` at egress). Mock-first: the keyring
backend is injected, so these tests touch NO real keychain. Rule-5: a secret VALUE never appears
in a repr/str/exception surface — only provider NAMES.
"""

from __future__ import annotations

import logging

import pytest
from keyring.errors import KeyringError

SECRET_TRIPO = "tk-live-TRIPOsecret9999"
SECRET_OPENAI = "sk-live-OPENAIsecret1234"


class _FakeKeyring:
    """In-memory recording fake of ``keyring.get_password(service, account) -> str | None``.

    Returns ``None`` for an absent account (mirrors keyring's missing-entry contract). Accounts
    listed in ``raise_on`` raise ``KeyringError`` instead — the locked/unavailable/denied path
    (on macOS a denied read raises ``KeyringLocked``, a ``KeyringError`` subclass). Records every
    call so a test can prove the injected backend (not the real keychain) was used.
    """

    def __init__(self, store: dict[str, str], *, raise_on: set[str] | None = None) -> None:
        self._store = store
        self._raise_on = raise_on or set()
        self.calls: list[tuple[str, str]] = []

    def __call__(self, service: str, account: str) -> str | None:
        self.calls.append((service, account))
        if account in self._raise_on:
            raise KeyringError("backend locked")  # message names NO secret value
        return self._store.get(account)


def test_get_reads_locked_in_named_entry() -> None:
    """spec(§18) — get(providerId) reads keyring at (service="AISimsCreator", account=providerId);
    the shared secret-name contract with the UI writer (7.2b-1)."""
    from obs.keychain_secrets import KEYCHAIN_SERVICE, KeychainSecretsAccessor

    backend = _FakeKeyring({"tripo": SECRET_TRIPO})
    acc = KeychainSecretsAccessor(["tripo"], get_password=backend)

    assert acc.get("tripo") == SECRET_TRIPO
    assert backend.calls == [(KEYCHAIN_SERVICE, "tripo")]


def test_get_absent_returns_none() -> None:
    """spec(§16) — an absent key returns None, not an error (the accessor contract)."""
    from obs.keychain_secrets import KeychainSecretsAccessor

    acc = KeychainSecretsAccessor(["tripo"], get_password=_FakeKeyring({}))

    assert acc.get("tripo") is None


def test_active_values_returns_live_values() -> None:
    """spec(§16) — over {tripo, openai} set + anthropic absent, active_values() yields the two
    live values in configured order (absent skipped); this is the redactor's egress-scrub input."""
    from obs.keychain_secrets import KeychainSecretsAccessor

    backend = _FakeKeyring({"tripo": SECRET_TRIPO, "openai": SECRET_OPENAI})
    acc = KeychainSecretsAccessor(["tripo", "openai", "anthropic"], get_password=backend)

    assert acc.active_values() == (SECRET_TRIPO, SECRET_OPENAI)


def test_active_values_dedups_duplicate_provider_ids() -> None:
    """spec(§16) — the configured provider set is conceptually unique: a provider id passed twice
    is read ONCE (no duplicate keychain reads, no double value in the redactor's scrub input)."""
    from obs.keychain_secrets import KEYCHAIN_SERVICE, KeychainSecretsAccessor

    backend = _FakeKeyring({"tripo": SECRET_TRIPO})
    acc = KeychainSecretsAccessor(["tripo", "tripo"], get_password=backend)

    assert acc.active_values() == (SECRET_TRIPO,)
    assert backend.calls == [(KEYCHAIN_SERVICE, "tripo")]  # read once, not twice


def test_repr_str_never_leak_values() -> None:
    """RULE-5 PIN — a live secret never appears in repr/str (which can land in a log/trace);
    repr shows provider NAMES only (mirrors InMemorySecretsAccessor)."""
    from obs.keychain_secrets import KeychainSecretsAccessor

    backend = _FakeKeyring({"tripo": SECRET_TRIPO})
    acc = KeychainSecretsAccessor(["tripo"], get_password=backend)

    acc.get("tripo")  # value retrieved at point of use...
    assert SECRET_TRIPO not in repr(acc)  # ...but never cached into a loggable surface
    assert SECRET_TRIPO not in str(acc)
    assert "tripo" in repr(acc)  # names ARE shown


def test_get_unavailable_backend_raises_typed_redacted() -> None:
    """spec(§16, RULE-5) — a locked/unavailable backend (KeyringError) surfaces a typed
    KeychainUnavailableError carrying the provider NAME only (no value, no raw cause); distinct
    from a legitimately-absent key (None)."""
    from obs.keychain_secrets import KeychainSecretsAccessor, KeychainUnavailableError

    backend = _FakeKeyring({"tripo": SECRET_TRIPO}, raise_on={"tripo"})
    acc = KeychainSecretsAccessor(["tripo"], get_password=backend)

    try:
        acc.get("tripo")
    except KeychainUnavailableError as exc:
        assert SECRET_TRIPO not in str(exc)  # value never in the error surface
        assert "tripo" in str(exc)  # name names the failing provider
        assert exc.__cause__ is None  # fresh error — no raw keyring cause chained
    else:
        raise AssertionError("expected KeychainUnavailableError on a locked backend")


def test_active_values_fail_safe_on_unavailable() -> None:
    """spec(§16) — active_values() is FAIL-SAFE for the redactor: a provider whose read raises
    is skipped (never propagated), so the redactor always gets a tuple and keeps functioning."""
    from obs.keychain_secrets import KeychainSecretsAccessor

    backend = _FakeKeyring({"tripo": SECRET_TRIPO, "openai": SECRET_OPENAI}, raise_on={"openai"})
    acc = KeychainSecretsAccessor(["tripo", "openai"], get_password=backend)

    assert acc.active_values() == (SECRET_TRIPO,)


def test_no_secret_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    """RULE-5 PIN (parity with desktop Lesson 8 secret-canary) — across get / active_values / the
    unavailable path, a live secret value appears in NO captured log output. Completes the
    "no leak on ANY surface" guarantee (repr/str + exception + LOG sinks)."""
    from obs.keychain_secrets import KeychainSecretsAccessor, KeychainUnavailableError

    # tripo reads OK; openai is present in the store but its read RAISES (locked) — exercises the
    # successful-read, the fail-safe active_values skip, AND the unavailable get() path.
    backend = _FakeKeyring({"tripo": SECRET_TRIPO, "openai": SECRET_OPENAI}, raise_on={"openai"})
    acc = KeychainSecretsAccessor(["tripo", "openai"], get_password=backend)

    with caplog.at_level(logging.DEBUG):
        acc.get("tripo")
        acc.active_values()
        try:
            acc.get("openai")
        except KeychainUnavailableError:
            pass

    # Lock "the accessor logs NOTHING at all" as the contract — a future refactor that adds any
    # log line (let alone one carrying a value) breaks this and forces a re-review.
    assert caplog.text == ""
    assert SECRET_TRIPO not in caplog.text
    assert SECRET_OPENAI not in caplog.text


def test_satisfies_secrets_accessor_protocol() -> None:
    """spec(§16) — KeychainSecretsAccessor is a structural SecretsAccessor (drop-in for the
    redactor) with zero edits to obs/secrets.py; the typed binding holds under mypy --strict."""
    from obs.keychain_secrets import KeychainSecretsAccessor
    from obs.secrets import SecretsAccessor

    acc: SecretsAccessor = KeychainSecretsAccessor(["tripo"], get_password=_FakeKeyring({}))

    # the typed binding above is the load-bearing mypy --strict structural check; these pin the
    # runtime return contract (str | None and tuple[str, ...]) over an empty backend.
    assert acc.get("tripo") is None
    assert acc.active_values() == ()


def test_service_constant_is_aisims_creator() -> None:
    """The service constant == "AISimsCreator" — the cross-process contract with the UI writer's
    apps/desktop/electron/keychain.ts:KEYCHAIN_SERVICE (must stay byte-identical both ends)."""
    from obs.keychain_secrets import KEYCHAIN_SERVICE

    assert KEYCHAIN_SERVICE == "AISimsCreator"


def test_backend_injected_no_real_keychain() -> None:
    """Mock-first (Track A) — the accessor reads through the INJECTED backend; the recording fake
    captures every (service, account) call (get + active_values), proving no real keyring backend
    was touched. The production default (keyring.get_password) is the real backend, swapped here."""
    from obs.keychain_secrets import KEYCHAIN_SERVICE, KeychainSecretsAccessor

    backend = _FakeKeyring({"tripo": SECRET_TRIPO})
    acc = KeychainSecretsAccessor(["tripo"], get_password=backend)

    acc.get("tripo")
    acc.active_values()

    assert backend.calls == [(KEYCHAIN_SERVICE, "tripo"), (KEYCHAIN_SERVICE, "tripo")]

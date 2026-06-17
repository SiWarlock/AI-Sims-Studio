"""RED — [SAFETY · RULE 5 · PINNED · NON-DROPPABLE] §16/§17 redaction chokepoint.

The redactor scrubs BOTH free-text ErrorEnvelope fields (creatorMessage + maintainerDetail) before
any egress — by registered active secret value AND by the enumerated secret/PII pattern set —
fail-CLOSED (a redaction error drops the field, never egresses it raw). The single secrets accessor
never leaks values into a loggable surface (forbidden-pattern 5).
"""

from __future__ import annotations

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope

SECRET = "sk-live-DEADBEEFcafe1234"


def test_redaction_scrubs_both_errorenvelope_fields() -> None:
    """spec(§16/§17, rule 5, PINNED) — a secret injected into BOTH creatorMessage AND
    maintainerDetail is gone post-redaction; asserts BOTH fields by name. NON-WAIVABLE."""
    from adapters.mock.failure import envelope_for  # 0.8 egress-realistic fixture base
    from obs.redaction import Redactor
    from obs.secrets import InMemorySecretsAccessor

    base = envelope_for(ErrorCode.PROVIDER_AUTH_QUOTA)
    env = base.model_copy(
        update={
            "creatorMessage": f"please retry; internal token {SECRET} was rejected",
            "maintainerDetail": f"raw provider body — Authorization: Bearer {SECRET}",
        }
    )
    redactor = Redactor(InMemorySecretsAccessor({"provider_key": SECRET}))
    out = redactor.redact_envelope(env)

    assert SECRET not in out.creatorMessage
    assert SECRET not in out.maintainerDetail


def test_redaction_scrubs_by_pattern_without_accessor() -> None:
    """spec(§16) — the enumerated secret/PII pattern set scrubs key-shaped tokens even when they
    are not registered active secret values."""
    from obs.redaction import Redactor
    from obs.secrets import InMemorySecretsAccessor

    redactor = Redactor(InMemorySecretsAccessor({}))  # no registered secrets
    out = redactor.redact_text("leaked AKIAIOSFODNN7EXAMPLE and sk-test-abc123def456ghi in a log")

    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "sk-test-abc123def456ghi" not in out


def test_redaction_also_scrubs_suggested_action() -> None:
    """spec(§16, defense-in-depth) — suggestedAction (the 3rd free-text field, egressed in the SSE
    error event) is pattern-scrubbed too; the chokepoint doesn't trust a fat-fingered producer."""
    from obs.redaction import Redactor
    from obs.secrets import InMemorySecretsAccessor

    env = ErrorEnvelope(
        code=ErrorCode.SYSTEM,
        category=ErrorCategory.SYSTEM,
        retryable=False,
        creatorMessage="ok",
        maintainerDetail="ok",
        suggestedAction="rotate AKIAIOSFODNN7EXAMPLE in Settings",
    )
    out = Redactor(InMemorySecretsAccessor({})).redact_envelope(env)
    assert out.suggestedAction is not None
    assert "AKIAIOSFODNN7EXAMPLE" not in out.suggestedAction


def test_redaction_span_redacts_nested_values() -> None:
    """spec(§16) — redact_span recurses into nested dicts/lists, so a secret in a span's
    attributes/events payload never egresses (not just top-level strings)."""
    from obs.redaction import Redactor
    from obs.secrets import InMemorySecretsAccessor

    redactor = Redactor(InMemorySecretsAccessor({}))
    span = {
        "name": "llm-node",
        "attributes": {"prompt": "use AKIAIOSFODNN7EXAMPLE", "nested": {"k": "sk-live-abc123def"}},
        "events": ["header Bearer sk-test-zzz999aaa111"],
    }
    flat = str(redactor.redact_span(span))

    assert "AKIAIOSFODNN7EXAMPLE" not in flat
    assert "sk-live-abc123def" not in flat
    assert "sk-test-zzz999aaa111" not in flat


def test_redaction_fail_closed() -> None:
    """spec(§16) — if redaction can't run, the field is placeholdered, NEVER egressed raw
    (distinct from tracing's fail-OPEN: a trace may drop, but a secret never leaks)."""
    from obs.redaction import REDACTION_FAILED_PLACEHOLDER, Redactor
    from obs.secrets import InMemorySecretsAccessor

    class _BoomRedactor(Redactor):
        def redact_text(self, text: str) -> str:
            raise RuntimeError("redactor exploded")

    env = ErrorEnvelope(
        code=ErrorCode.SYSTEM,
        category=ErrorCategory.SYSTEM,
        retryable=False,
        creatorMessage=f"secret {SECRET}",
        maintainerDetail=f"secret {SECRET}",
    )
    out = _BoomRedactor(InMemorySecretsAccessor({})).redact_envelope(env)

    assert out.creatorMessage == REDACTION_FAILED_PLACEHOLDER
    assert out.maintainerDetail == REDACTION_FAILED_PLACEHOLDER
    assert SECRET not in out.creatorMessage and SECRET not in out.maintainerDetail


def test_secrets_accessor_never_persists() -> None:
    """spec(§16 / fp-5) — the accessor yields a secret via get() but never leaks the value into a
    repr/str surface that could land in a log or trace."""
    from obs.secrets import InMemorySecretsAccessor

    acc = InMemorySecretsAccessor({"provider_key": SECRET})
    assert acc.get("provider_key") == SECRET  # retrievable at point of use
    assert SECRET not in repr(acc)  # never in a loggable repr
    assert SECRET not in str(acc)
    assert acc.get("missing") is None

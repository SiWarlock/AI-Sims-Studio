"""[SAFETY · RULE 5 · PINNED] §16/§17 redaction chokepoint.

The single egress redactor. It scrubs (a) every live secret VALUE (from the secrets accessor, by
substring replace — every occurrence, never whole-field equality) and (b) an enumerated secret/PII
PATTERN set (key shapes). It is applied to BOTH ``ErrorEnvelope`` free-text fields
(``creatorMessage`` + ``maintainerDetail``) — the PINNED, non-waivable rule-5 surface — plus
``suggestedAction`` (defense-in-depth: the 3rd SSE-egressed free-text field).

**Fail-CLOSED** (distinct from tracing's fail-OPEN): if redaction raises, the field is replaced with
a placeholder — a raw free-text field is NEVER egressed unredacted. (A trace may be dropped to never
block a run; a secret is never leaked.)
"""

from __future__ import annotations

import re
from typing import Any

from aisims_contracts.error import ErrorEnvelope

from .secrets import SecretsAccessor

REDACTION_PLACEHOLDER = "[REDACTED]"
REDACTION_FAILED_PLACEHOLDER = "[REDACTION-FAILED]"

# Enumerated secret/PII pattern set (§16) — a best-effort net for UNREGISTERED key shapes.
# NON-EXHAUSTIVE by design: the GUARANTEE is accessor registration (active_values substring scrub);
# every live key MUST flow through the SecretsAccessor (Phase-7 keychain). Patterns are
# defense-in-depth for a producer that fat-fingers an unregistered token into free text.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk[-_][A-Za-z0-9._-]{6,}"),  # OpenAI / Anthropic / Stripe sk- or sk_ keys
    re.compile(r"AKIA[0-9A-Z]{12,}"),  # AWS access key id
    re.compile(r"AIza[A-Za-z0-9._-]{10,}"),  # Google API key
    re.compile(r"eyJ[A-Za-z0-9._-]{10,}"),  # JWT (base64 header starts "eyJ")
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._-]{6,}"),  # bearer tokens (case-insensitive)
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),  # GitHub tokens
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),  # Slack bot/user tokens
    re.compile(r"xapp-[A-Za-z0-9-]{10,}"),  # Slack app tokens
)


class Redactor:
    def __init__(
        self,
        secrets: SecretsAccessor,
        *,
        patterns: tuple[re.Pattern[str], ...] = _SECRET_PATTERNS,
    ) -> None:
        self._secrets = secrets
        self._patterns = patterns

    def redact_text(self, text: str) -> str:
        """Scrub live secret values (substring) + enumerated patterns from ``text``."""
        out = text
        for value in self._secrets.active_values():
            if value:
                out = out.replace(value, REDACTION_PLACEHOLDER)
        for pattern in self._patterns:
            out = pattern.sub(REDACTION_PLACEHOLDER, out)
        return out

    def _safe_redact(self, text: str) -> str:
        try:
            return self.redact_text(text)
        except Exception:
            return REDACTION_FAILED_PLACEHOLDER  # fail-closed: never egress raw

    def redact_envelope(self, env: ErrorEnvelope) -> ErrorEnvelope:
        """Scrub the egress-bearing free-text fields (PINNED: creatorMessage + maintainerDetail;
        defense-in-depth: suggestedAction). Fail-closed per field."""
        updates: dict[str, str] = {
            "creatorMessage": self._safe_redact(env.creatorMessage),
            "maintainerDetail": self._safe_redact(env.maintainerDetail),
        }
        if env.suggestedAction is not None:
            updates["suggestedAction"] = self._safe_redact(env.suggestedAction)
        return env.model_copy(update=updates)

    def redact_span(self, span: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact every string in a trace span before egress (§14 → §16 chokepoint).

        Spans carry nested payloads (e.g. an OTEL/LangSmith ``attributes`` dict or an ``events``
        list), so a shallow top-level walk would leak a nested secret — recurse into dicts + lists.
        """
        return {key: self._redact_value(value) for key, value in span.items()}

    def _redact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._safe_redact(value)
        if isinstance(value, dict):
            return {k: self._redact_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._redact_value(item) for item in value]
        return value

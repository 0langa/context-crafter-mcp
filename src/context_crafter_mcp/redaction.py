"""Generated-output redaction helpers."""

from __future__ import annotations

import re
from pathlib import Path

REDACTION_MARKER = "[REDACTED]"

_SENSITIVE_KEY_NAMES = (
    r"api[_-]?key",
    r"secret",
    r"token",
    r"password",
    r"passwd",
    r"pwd",
    r"private[_-]?key",
    r"access[_-]?token",
    r"refresh[_-]?token",
    r"client[_-]?secret",
)
_KEY_ALT = "|".join(_SENSITIVE_KEY_NAMES)

_JSON_VALUE_PATTERNS = [
    re.compile(rf'("({_KEY_ALT})"\s*:\s*")([^"]+)(")', re.IGNORECASE),
]
_ASSIGNMENT_PATTERNS = [
    re.compile(rf"(\b({_KEY_ALT})\b\s*[:=]\s*['\"]?)([^'\"\s,}}\]]{{4,}})(['\"]?)", re.IGNORECASE),
]
_TOKEN_PATTERNS = [
    re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\b(sk-proj-[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9_]{8,})\b"),
]


def redact_sensitive_text(text: str) -> str:
    """Redact obvious secret-looking values from generated output text.

    This is a conservative last-mile guard for generated artifacts. It does not
    replace dedicated secret scanning, but it prevents common key/value secrets
    from being echoed into Markdown, JSON, Mermaid, or HTML outputs.
    """
    redacted = text
    for pattern in _JSON_VALUE_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}{REDACTION_MARKER}{match.group(4)}", redacted)
    for pattern in _ASSIGNMENT_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}{REDACTION_MARKER}{match.group(4)}", redacted)
    redacted = _TOKEN_PATTERNS[0].sub(lambda match: f"{match.group(1)}{REDACTION_MARKER}", redacted)
    for pattern in _TOKEN_PATTERNS[1:]:
        redacted = pattern.sub(REDACTION_MARKER, redacted)
    return redacted


def write_redacted_text(path: Path, text: str) -> None:
    """Write generated text after applying the redaction guard."""
    path.write_text(redact_sensitive_text(text), encoding="utf-8")

"""Secret redaction (defence in depth: the extension redacts first, the daemon again)."""
import re

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[REDACTED:private-key]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED:aws-key]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "[REDACTED:github-token]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"), "[REDACTED:api-key]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"), "[REDACTED:slack-token]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"), "[REDACTED:jwt]"),
    # name = "literal secret"  /  "password": 'hunter2'
    (re.compile(r"""\b([\w.-]*(?:api[_-]?key|secret|token|passw(?:or)?d|pwd)[\w.-]*)(["']?\s*[:=]\s*)(['"])([^'"\n]{4,})\3""", re.I),
     r"\1\2\3[REDACTED]\3"),
    # .env style: SOME_SECRET=value
    (re.compile(r"""^([ \t]*[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD)[A-Z0-9_]*[ \t]*=[ \t]*)(?!['"])\S+""", re.M),
     r"\1[REDACTED]"),
]


def redact(text: str) -> str:
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text

"""Contract 3 (Finding) as a dataclass. `to_dict()` emits exactly the contract fields."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict

KINDS = ("test_failure", "diagnostic", "pattern", "guess_spam")


@dataclass
class Finding:
    kind: str
    mistake_id: str
    concept_ids: list
    file: str
    line: int                   # 1-based; 0 when unknown (e.g. a hidden test with no stack frame)
    evidence: str
    confidence: float
    lesson_id: str | None = None

    def __post_init__(self):
        assert self.kind in KINDS, self.kind
        self.confidence = round(max(0.0, min(1.0, float(self.confidence))), 2)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Hit:
    """Internal result of a language-neutral rule, before it is mapped to a lesson's mistake_id."""
    rule: str
    line: int
    evidence: str
    confidence: float
    key: str = ""               # stable identity of the flagged code, for de-duplication

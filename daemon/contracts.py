"""Canonical Pydantic v2 schemas for Socratic Code-Tutor Pet.

Validates and normalizes all data crossing module boundaries:
1. Editor event (extension -> daemon, WS /ws/editor)
2. Test result (analysis.run_tests)
3. Finding (analysis -> tutor)
4. Tutor output (tutor -> UI)
5. UI websocket channels & REST payloads (/ws/ui, /api/progress, /api/review)
6. Lesson manifest data (lesson.yaml)
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

# Valid pet states across UI, daemon, and tutor
PET_STATES = (
    "idle",
    "curious",
    "thinking",
    "asking",
    "celebrating",
    "sleeping",
    "stressed",
    "detective",
)
PetStateType = Literal[
    "idle",
    "curious",
    "thinking",
    "asking",
    "celebrating",
    "sleeping",
    "stressed",
    "detective",
]

# Supported modes
MODES = ("dsa", "system_design")
ModeType = Literal["dsa", "system_design"]

# Finding kinds
FINDING_KINDS = ("test_failure", "diagnostic", "pattern", "guess_spam")
FindingKindType = Literal["test_failure", "diagnostic", "pattern", "guess_spam"]


# ------------------------------------------------------------- 1. Editor Event
class CursorPos(BaseModel):
    line: int
    col: int


class SelectionRange(BaseModel):
    start: CursorPos
    end: CursorPos


class DiagnosticItem(BaseModel):
    line: int = 1
    severity: str = "error"
    message: str = ""


class EditorEvent(BaseModel):
    type: Literal["edit", "focus", "cursor", "diagnostics", "test_run", "file_open"]
    ts: int = Field(default_factory=lambda: int(time.time()))
    file: str = ""
    language: str = "python"
    student_id: str = "local-user"
    content: Optional[str] = None
    cursor: Optional[CursorPos] = None
    selection: Optional[SelectionRange] = None
    diagnostics: Optional[List[DiagnosticItem]] = None
    action: Optional[Literal["open", "close"]] = None
    test_result: Optional[Dict[str, Any]] = None


# ------------------------------------------------------------- 2. Test Result
class TestCaseResult(BaseModel):
    name: str
    passed: bool
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    error_type: Optional[str] = None
    message: str = ""
    hidden: bool = False


class TestResult(BaseModel):
    lesson_id: str
    language: str
    duration_ms: int = 0
    results: List[TestCaseResult] = Field(default_factory=list)
    all_passed: bool = False

    @model_validator(mode="before")
    @classmethod
    def compute_all_passed(cls, data: Any) -> Any:
        if isinstance(data, dict):
            results = data.get("results") or []
            if "all_passed" not in data:
                data["all_passed"] = bool(results) and all(
                    r.get("passed", False) if isinstance(r, dict) else getattr(r, "passed", False)
                    for r in results
                )
        return data


# ----------------------------------------------------------------- 3. Finding
class Finding(BaseModel):
    kind: FindingKindType = "test_failure"
    mistake_id: str
    concept_ids: List[str] = Field(default_factory=list)
    file: str = ""
    line: int = 0
    evidence: str = ""
    confidence: float = 0.9
    lesson_id: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return round(max(0.0, min(1.0, float(v))), 2)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# ------------------------------------------------------------- 4. Tutor Output
class GraphNode(BaseModel):
    id: str
    label: str = "Concept"
    props: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    type: str = "INVOLVES"

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "source" in data and "from" not in data and "from_node" not in data:
                data["from"] = data.pop("source")
            if "target" in data and "to" not in data and "to_node" not in data:
                data["to"] = data.pop("target")
        return data


class GraphTrace(BaseModel):
    cypher: str = ""
    query_ms: Optional[float] = None
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


class TutorOutput(BaseModel):
    question: str
    hint_level: int = Field(ge=0, le=4, default=0)
    targets_concept: Optional[str] = None
    mistake_id: Optional[str] = None
    pet_state: PetStateType = "asking"
    graph_trace: Optional[GraphTrace] = None

    @field_validator("question")
    @classmethod
    def clean_question(cls, v: str) -> str:
        text = (v or "").strip()
        if "```" in text:
            # Code safeguard fallback
            return "Walk me through what you expect this part to do on the smallest input you can think of."
        return text[:600]


# ------------------------------------------------- 5. UI Websockets & REST
class EvolutionInfo(BaseModel):
    stage: int = 1
    variant: Literal["blob", "wizard", "dragon"] = "blob"
    stage_name: str = "Novice"
    next_stage_name: Optional[str] = "Apprentice"
    progress: float = 0.0
    streak: int = 1
    mastery_total: float = 0.0
    next: Optional[Dict[str, Any]] = None


class GraphHighlight(BaseModel):
    node_ids: List[str] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    reason: Optional[str] = None


class GraphUpdatePayload(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    highlight: Optional[GraphHighlight] = None


class MasteryUpdatePayload(BaseModel):
    concept_id: str
    mastery: float
    delta: float = 0.0
    evolution: Optional[EvolutionInfo] = None


class ReviewAxis(BaseModel):
    id: str
    label: str
    score: float
    max: float = 5.0


class ReviewPayload(BaseModel):
    design_id: str
    axes: List[ReviewAxis] = Field(default_factory=list)
    notes: Optional[List[str]] = None


class ProgressConcept(BaseModel):
    id: str
    name: str
    track: str = "dsa"
    mastery: float = 0.0


class ProgressLesson(BaseModel):
    id: str
    title: str
    track: str = "dsa"
    status: Literal["not_started", "in_progress", "done"] = "not_started"
    progress: float = 0.0


class Progress(BaseModel):
    mode: Optional[ModeType] = "dsa"
    streak: Dict[str, int] = Field(default_factory=lambda: {"current": 1, "best": 1})
    daily_activity: List[Dict[str, Any]] = Field(default_factory=list)
    skill_radar: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    concepts: List[ProgressConcept] = Field(default_factory=list)
    recent_mistakes: List[Dict[str, Any]] = Field(default_factory=list)
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    hint_dependency: List[Dict[str, Any]] = Field(default_factory=list)
    lessons: List[ProgressLesson] = Field(default_factory=list)
    recommended_next: Optional[Dict[str, str]] = None
    spaced_repetition_due: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    evolution: EvolutionInfo = Field(default_factory=EvolutionInfo)

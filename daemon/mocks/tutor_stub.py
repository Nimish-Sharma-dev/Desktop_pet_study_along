"""STUB for C's tutor engine. Returns canned Socratic questions (never code) plus a fake graph trace."""
from collections import defaultdict

_Q = {
    "boundary_off_by_one": [
        "What happens to your loop when the list has exactly one element?",
        "Which index does your last iteration touch, and is that index valid?",
        "If you wrote the smallest list your code might mishandle, which line would first misbehave?",
    ],
    "syntax_error": ["Your editor is flagging something near that line. What do you think it expects to see there?"],
    "wrong_output": ["Pick the failing test. What value did you expect, and what path through your code produces the other one?"],
    "loop_invariants": ["What is always true at the top of each iteration of your loop?"],
    "complexity_blindspot": ["If the input grows 10x, roughly how many times does your inner loop body run?"],
    "missing_base_case": ["What is the smallest input this function receives, and what should it return for it?"],
}
_DEFAULT = ["Can you explain, in one sentence, what this part is meant to guarantee?"]
_count: dict = defaultdict(int)


def _trace(mid, concepts, lesson_id):
    nodes = [{"id": f"m:{mid}", "label": "Mistake", "props": {"name": mid}},
             {"id": f"l:{lesson_id}", "label": "Lesson", "props": {"id": lesson_id}}]
    edges = [{"from": f"m:{mid}", "to": f"l:{lesson_id}", "type": "OBSERVED_IN"}]
    for c in concepts:
        nodes.append({"id": f"c:{c}", "label": "Concept", "props": {"name": c}})
        edges.append({"from": f"m:{mid}", "to": f"c:{c}", "type": "INVOLVES"})
    return {"cypher": "MATCH (m:Mistake {name:$mid})-[:INVOLVES]->(c:Concept) RETURN m, c",
            "query_ms": 3.2, "nodes": nodes, "edges": edges}


def handle(finding, student_id):
    mid = finding.get("mistake_id", "unknown")
    qs = _Q.get(mid, _DEFAULT)
    level = _count[(student_id, mid)]
    _count[(student_id, mid)] += 1
    concepts = finding.get("concept_ids") or []
    return {"question": qs[min(level, len(qs) - 1)], "hint_level": min(level, 4),
            "targets_concept": concepts[0] if concepts else None, "mistake_id": mid,
            "pet_state": "asking", "graph_trace": _trace(mid, concepts, finding.get("lesson_id", "demo"))}


def handle_reply(text, student_id, last_finding):
    """Optional extension to the contract (see README): C may implement a real one."""
    f = last_finding or {}
    mid = f.get("mistake_id")
    level = min(_count[(student_id, mid)] + 1, 4)
    _count[(student_id, mid)] = level
    return {"question": "Interesting. What would a test look like that proves that, one way or the other?",
            "hint_level": level, "targets_concept": (f.get("concept_ids") or [None])[0],
            "mistake_id": mid, "pet_state": "asking",
            "graph_trace": _trace(mid, f.get("concept_ids") or [], f.get("lesson_id", "demo")) if mid else None}

"""
Socratic Tutor Engine for Team C.

Orchestrates pedagogical decision-making:
- Identifies root bottleneck concepts via backward dependency traversal.
- Queries student mistake memory to detect recurrence and guess-spamming.
- Computes progressive hint level (L0 to L4; L0 for guess-spamming).
- Retrieves relevant conceptual chunks via hybrid graph+vector search.
- Prompts local Qwen (qwen2.5-coder:7b via Ollama) with strict Socratic guidelines.
- Enforces output safety through guardrail retries and seed question fallback.
- Returns Contract 4 structured JSON payload with full graph telemetry.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

try:
    from falkordb import Graph
except ImportError:
    Graph = Any  # type: ignore[misc,assignment]

try:
    from daemon.graph.retrieval import (
        find_bottleneck,
        hybrid_query,
        query_pattern_memory,
    )
    from daemon.graph.schema import get_client, get_graph
    from daemon.tutor.guard import guard_check
except ImportError:
    from graph.retrieval import (
        find_bottleneck,
        hybrid_query,
        query_pattern_memory,
    )
    from graph.schema import get_client, get_graph
    from tutor.guard import guard_check

logger = logging.getLogger(__name__)

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5-coder:7b"
MAX_GUARD_RETRIES = 3

# Seed questions repository for deterministic fallbacks and high-confidence scaffolding
SEED_QUESTIONS_POOL: Dict[str, Dict[int, str]] = {
    "boundary_off_by_one": {
        0: "Take a step back. What is the fundamental boundary condition you are trying to verify?",
        1: "What loop invariant guarantees that every valid index in the search space is inspected?",
        2: "Consider what happens when the search window reduces to left == right. Does your loop still execute?",
        3: "If the target element was at index 0 or the very last index, which branch in your condition would handle it?",
        4: "Trace a single-element list: what values do left, right, and mid take on the very first iteration?",
    },
    "infinite_loop": {
        0: "Take a pause. What condition in your logic guarantees that this repetition eventually stops?",
        1: "How does each iteration bring the pointers or counters strictly closer to the termination state?",
        2: "When the pointers become adjacent, does updating your boundary variables guarantee the window shrinks?",
        3: "What happens when left + 1 == right and the search condition is evaluated?",
        4: "Trace pointer movements: if neither boundary updates in a branch, why did the loop fail to progress?",
    },
    "array_indexing": {
        0: "Think about the coordinate system: what are the legal index boundaries for an array of size N?",
        1: "Which index represents the final valid element in a zero-indexed sequence?",
        2: "Could an offset or midpoint calculation ever compute an index outside the allocated length?",
        3: "How should your code behave if the input collection contains zero elements?",
        4: "What exact index is being calculated and accessed when the error occurs?",
    },
    "guess_spam": {
        0: "Take a deep breath and pause for a moment. Before modifying another line, what specific state is causing the current test to fail?",
        1: "What invariant are you trying to test with this change?",
        2: "What was the exact outcome of the previous attempt compared to this one?",
        3: "Can you write down the expected state after line 1 before running the test again?",
        4: "What specific hypothesis are you testing right now?",
    },
}

GENERIC_SEED_QUESTIONS: Dict[int, str] = {
    0: "Let's pause and take a step back. What is the overarching objective of this algorithm?",
    1: "What invariant or relationship must remain true before and after this block executes?",
    2: "Where does the actual execution trace begin to diverge from what you expected?",
    3: "How does your logic behave on the smallest valid edge case?",
    4: "Can you trace the variable values step-by-step for the failing input scenario?",
}


def _get_fallback_seed_question(
    mistake_id: str,
    concept_id: str,
    hint_level: int,
    line: Optional[int] = None,
) -> str:
    """Retrieve a curated, pre-validated Socratic seed question for fallback."""
    level = max(0, min(4, hint_level))

    # 1. Match specific mistake
    if mistake_id in SEED_QUESTIONS_POOL:
        q = SEED_QUESTIONS_POOL[mistake_id].get(level)
        if q:
            return q.format(line=line or "current")

    # 2. Match concept
    if concept_id in SEED_QUESTIONS_POOL:
        q = SEED_QUESTIONS_POOL[concept_id].get(level)
        if q:
            return q.format(line=line or "current")

    # 3. Generic fallback by hint level
    return GENERIC_SEED_QUESTIONS.get(level, GENERIC_SEED_QUESTIONS[0])


def _call_ollama_generate(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: float = 15.0,
) -> Optional[Dict[str, Any]]:
    """Send structured JSON generation request to local Ollama instance."""
    payload = json.dumps({
        "model": model,
        "system": system_prompt,
        "prompt": user_prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_response = data.get("response", "")
            if not raw_response:
                return None
            return json.loads(raw_response)
    except Exception as exc:
        logger.warning("Ollama generation call failed or timed out: %s", exc)
        return None


def handle_tutor(
    graph: Graph,
    finding: Dict[str, Any],
    student_id: str = "local-user",
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Handle a code analysis Finding and produce a Socratic TutorOutput (Contract 4).

    Steps:
    1. Query recurrence pattern memory and trace root prerequisite bottlenecks.
    2. Determine progressive hint level (0-4; guess_spam always receives L0).
    3. Retrieve relevant explanation chunks via hybrid vector+graph search.
    4. Call local Qwen model with JSON formatting and Socratic constraints.
    5. Pass output through guardrail check with retries, falling back to curated seed questions.
    6. Return Contract 4 JSON output containing graph telemetry.

    Args:
        graph: FalkorDB Graph instance.
        finding: Finding dictionary (Contract 3).
        student_id: Active student identifier (default: "local-user").
        model: Ollama model name (default: "qwen2.5-coder:7b").

    Returns:
        Contract 4 TutorOutput dictionary.
    """
    kind = finding.get("kind", "test_failure")
    mistake_id = finding.get("mistake_id") or "general_error"
    concept_ids = finding.get("concept_ids") or []
    primary_concept = concept_ids[0] if concept_ids else "logic"
    evidence = finding.get("evidence", "")
    line_number = finding.get("line")

    # Step 1: Check pattern frequency & bottleneck concept
    pattern_info = query_pattern_memory(graph, student_id, mistake_id)
    recurrence_count = pattern_info.get("recurrence_count", 0)

    bottleneck_info = find_bottleneck(graph, primary_concept)
    bottleneck_concept = bottleneck_info.get("bottleneck_concept_id", primary_concept)
    bottleneck_depth = bottleneck_info.get("depth", 0)

    # Focus on the root weakness bottleneck if identified along the dependency path
    targets_concept = bottleneck_concept if bottleneck_depth > 0 else primary_concept

    # Step 2: Determine progressive hint level (L0 to L4)
    # Rule: Guess spamming always receives Level 0 (metacognitive reflection pause)
    if kind == "guess_spam":
        hint_level = 0
        pet_state = "detective"
    else:
        # Scale hint level with mistake recurrence (L1 on first attempt, up to L4)
        hint_level = min(4, max(1, recurrence_count + 1))
        pet_state = "asking"

    # Step 3: Retrieve context chunks via hybrid search
    query_text = f"{evidence} {mistake_id} {targets_concept}".strip()
    hybrid_result = hybrid_query(graph, student_id, targets_concept, query_text, top_k=3)
    chunks_list = hybrid_result.get("chunks", [])

    context_snippets = []
    for c in chunks_list[:2]:
        content = c.get("content", "").strip()
        if content:
            context_snippets.append(f"- {content[:200]}")
    chunks_context = "\n".join(context_snippets) if context_snippets else "None available."

    # Step 4: Prepare Socratic Prompts
    hint_level_descriptions = {
        0: "Level 0: Metacognitive pause asking the student to reflect on their hypothesis or precondition without code.",
        1: "Level 1: Guiding question on invariants or core concept principles.",
        2: "Level 2: Attention-directing question towards the specific condition, pointer, or boundary.",
        3: "Level 3: Inquiry testing behavior under a specific edge-case input scenario.",
        4: "Level 4: Step-by-step walkthrough trace inquiry of the failing execution case.",
    }

    system_prompt = (
        "You are a friendly Socratic companion pet tutor. "
        "Your task is to guide a student to discover their coding error by asking ONE guiding question.\n"
        "STRICT PEDAGOGICAL RULES:\n"
        "1. NEVER give the solution, code fix, syntax replacement, variable assignment, or return statement.\n"
        "2. NEVER use direct directives such as 'change X to Y', 'replace X with Y', 'use X instead of Y', or 'set X to Y'.\n"
        "3. Focus on guiding the student's thinking at the requested hint level.\n"
        "4. Respond ONLY with a valid JSON object matching: {\"question\": \"...\", \"targets_concept\": \"...\"}."
    )

    user_prompt = f"""
Student Failure Context:
- Mistake ID: {mistake_id}
- Target Concept: {targets_concept}
- Hint Level: L{hint_level} ({hint_level_descriptions.get(hint_level)})
- Evidence / Error: {evidence}
- File/Line: {finding.get('file', 'solution')}:{line_number or 'N/A'}
- Conceptual Context:
{chunks_context}

Formulate ONE thoughtful Socratic guiding question at Hint Level {hint_level}.
Do NOT output code or instructions on what to write.
Respond strictly in JSON format: {{"question": "...", "targets_concept": "{targets_concept}"}}
""".strip()

    # Step 5: Query Ollama with Guardrail Retries
    question: Optional[str] = None
    resolved_target_concept = targets_concept

    for attempt in range(1, MAX_GUARD_RETRIES + 1):
        parsed = _call_ollama_generate(system_prompt, user_prompt, model=model)
        if parsed and isinstance(parsed, dict):
            candidate_q = parsed.get("question")
            candidate_concept = parsed.get("targets_concept")

            if candidate_q and isinstance(candidate_q, str):
                is_safe, reason = guard_check(candidate_q)
                if is_safe:
                    question = candidate_q.strip()
                    if candidate_concept:
                        resolved_target_concept = str(candidate_concept).strip()
                    logger.debug("Ollama question passed guard check on attempt %d", attempt)
                    break
                else:
                    logger.warning("Ollama output rejected by guardrail on attempt %d: %s", attempt, reason)
                    # Append guard feedback to user prompt for next retry
                    user_prompt += f"\nPrevious attempt was rejected because it {reason}. Please rephrase as a purely conceptual question."

    # Fallback to pre-validated Socratic seed question if LLM unavailable or rejected
    if not question:
        logger.info("Using curated Socratic seed question fallback for %s at level %d", mistake_id, hint_level)
        question = _get_fallback_seed_question(mistake_id, targets_concept, hint_level, line_number)

    # Step 6: Return Contract 4 JSON output with graph trace
    return {
        "question": question,
        "hint_level": hint_level,
        "targets_concept": resolved_target_concept,
        "mistake_id": mistake_id,
        "pet_state": pet_state,
        "graph_trace": {
            "cypher": hybrid_result.get("cypher", ""),
            "query_ms": hybrid_result.get("query_ms", 0.0),
            "nodes": hybrid_result.get("nodes", []),
            "edges": hybrid_result.get("edges", []),
        },
    }


def handle(
    finding: Dict[str, Any],
    student_id: str = "local-user",
    graph: Optional[Graph] = None,
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Standard daemon entry point matching `tutor.handle(finding, student_id) -> TutorOutput`.

    Args:
        finding: Finding dictionary (Contract 3).
        student_id: Active student identifier.
        graph: Optional active FalkorDB Graph instance. If None, connects to default graph.
        model: Local LLM model tag.

    Returns:
        Contract 4 TutorOutput dictionary.
    """
    if graph is None:
        client = get_client()
        graph = get_graph(client)

    return handle_tutor(graph=graph, finding=finding, student_id=student_id, model=model)

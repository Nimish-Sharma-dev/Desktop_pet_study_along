"""
Graph and persistence layer for Socratic Code-Tutor Pet (Team C).
"""

from daemon.graph.ingest import (
    embed_text,
    ingest_lesson,
    record_attempt,
    update_mastery,
)
from daemon.graph.retrieval import (
    find_bottleneck,
    hybrid_query,
    query_pattern_memory,
)
from daemon.graph.schema import (
    DEFAULT_GRAPH_NAME,
    DEFAULT_HOST,
    DEFAULT_PORT,
    get_client,
    get_graph,
    init_schema,
)

__all__ = [
    "DEFAULT_GRAPH_NAME",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "get_client",
    "get_graph",
    "init_schema",
    "embed_text",
    "ingest_lesson",
    "record_attempt",
    "update_mastery",
    "hybrid_query",
    "find_bottleneck",
    "query_pattern_memory",
]

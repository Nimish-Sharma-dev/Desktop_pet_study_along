"""
Graph and persistence layer for Socratic Code-Tutor Pet (Team C).
"""

try:
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
except ImportError:
    from graph.ingest import (
        embed_text,
        ingest_lesson,
        record_attempt,
        update_mastery,
    )
    from graph.retrieval import (
        find_bottleneck,
        hybrid_query,
        query_pattern_memory,
    )
    from graph.schema import (
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

"""Affiliate Factory LangGraph pipelines.

Both graphs use the 'affiliate:*' thread namespace so their checkpoint rows
in the shared SQLite checkpoints.db never collide with the main orchestrator's
thread IDs (which use plain chat_id strings).

Canonical usage:
    from affiliate_factory.graphs import make_thread_id
    from affiliate_factory.graphs.daily_pipeline import build_daily_graph

    graph = build_daily_graph()
    thread_id = make_thread_id("daily", "2026-04-26")
    result = await graph.ainvoke(initial_state, {"configurable": {"thread_id": thread_id}})
"""

THREAD_NAMESPACE = "affiliate"


def make_thread_id(graph_type: str, identifier: str) -> str:
    """Build a namespaced thread ID for LangGraph checkpointing.

    Args:
        graph_type:  'daily' | 'weekly' (or any custom string).
        identifier:  Unique run identifier, typically a date string
                     (YYYY-MM-DD) or week string (YYYY-W15).

    Returns:
        String of the form 'affiliate:<graph_type>:<identifier>'.

    Examples:
        make_thread_id("daily", "2026-04-26")  → "affiliate:daily:2026-04-26"
        make_thread_id("weekly", "2026-W17")   → "affiliate:weekly:2026-W17"
    """
    return f"{THREAD_NAMESPACE}:{graph_type}:{identifier}"


__all__ = ["THREAD_NAMESPACE", "make_thread_id"]

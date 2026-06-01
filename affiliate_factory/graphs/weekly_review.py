"""Weekly Review — LangGraph StateGraph for performance analysis and optimisation.

Execution order:
    collect_performance
        ↓
    identify_winners
        ↓
    extract_patterns      (OptimizerAgent)
        ↓
    update_knowledge_base  (persist patterns to ChromaDB for next week's pipeline)
        ↓
    generate_report        (Telegram-ready Markdown summary)

Thread namespace: affiliate:weekly:YYYY-WNN
Example:          affiliate:weekly:2026-W17

The graph reads exclusively from SQLite and ChromaDB — it does not post to
any external platform.  Its output (the Markdown report) is sent to the
authorized Telegram user via /affiliate_weekly.

Usage:
    from affiliate_factory.graphs.weekly_review import build_weekly_graph
    from affiliate_factory.graphs import make_thread_id

    graph = build_weekly_graph()
    state = WeeklyReviewState(week_start="2026-04-20", week_end="2026-04-26")
    result = await graph.ainvoke(
        state,
        {"configurable": {"thread_id": make_thread_id("weekly", "2026-W17")}}
    )
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from affiliate_factory.graphs import THREAD_NAMESPACE, make_thread_id
from typing_extensions import TypedDict


# ── State ─────────────────────────────────────────────────────────────────────


class WeeklyReviewState(TypedDict):
    """Full mutable state passed between weekly review nodes."""

    week_start: str                          # YYYY-MM-DD (Monday)
    week_end: str                            # YYYY-MM-DD (Sunday)
    videos_this_week: list[dict[str, Any]]   # video rows from SQLite
    performance_data: list[dict[str, Any]]   # aggregated metrics per video
    winners: list[dict[str, Any]]            # top performers above threshold
    patterns_new: list[dict[str, Any]]       # patterns extracted by OptimizerAgent
    patterns_updated: list[dict[str, Any]]   # existing patterns with new evidence
    recommendations: list[str]               # actionable next-week suggestions
    report_markdown: str                     # Telegram-ready summary
    status: str                              # pending | done | failed
    errors: list[str]


# ── Node stubs ────────────────────────────────────────────────────────────────


async def node_collect_performance(state: WeeklyReviewState) -> dict[str, Any]:
    """Query SQLite for all videos + performance rows in the week window.

    Returns:
        Partial state: {"videos_this_week": [...], "performance_data": [...], "errors": [...]}
    """
    ...


async def node_identify_winners(state: WeeklyReviewState) -> dict[str, Any]:
    """Filter performance_data to isolate winner candidates.

    Winner threshold (initial): views > 10_000 OR conversions > 0.
    Threshold is intentionally low at launch; tuned via winners_pattern table.

    Returns:
        Partial state: {"winners": [...], "errors": [...]}
    """
    ...


async def node_extract_patterns(state: WeeklyReviewState) -> dict[str, Any]:
    """Invoke OptimizerAgent to extract patterns from winners.

    Returns:
        Partial state: {"patterns_new": [...], "patterns_updated": [...], "errors": [...]}
    """
    ...


async def node_update_knowledge_base(state: WeeklyReviewState) -> dict[str, Any]:
    """Persist new/updated patterns to SQLite winners_pattern + ChromaDB passages.

    Returns:
        Partial state: {"errors": [...]}
    """
    ...


async def node_generate_report(state: WeeklyReviewState) -> dict[str, Any]:
    """Render a Telegram-ready Markdown report from the week's findings.

    Report sections:
      - Weekly KPIs (total views, conversions, revenue estimate)
      - Top 3 videos with metrics
      - New patterns discovered
      - Recommendations for next week

    Returns:
        Partial state: {"report_markdown": str, "status": "done", "errors": [...]}
    """
    ...


# ── Graph builder ─────────────────────────────────────────────────────────────


def build_weekly_graph() -> StateGraph:
    """Assemble and compile the weekly review StateGraph.

    Returns:
        Compiled LangGraph StateGraph ready for ainvoke / invoke.
    """
    ...

"""Daily Pipeline — LangGraph StateGraph for autonomous brief production.

Execution order:
    mine_trends
        ↓
    research_offers  ←──── (parallel with mine_trends if feasible)
        ↓
    scout_competitors
        ↓
    build_brief
        ↓
    forge_script
        ↓
    generate_visuals
        ↓
    write_captions
        ↓
    finalize_brief     (persists brief_id + script + visuals + captions to SQLite)

The graph is fault-tolerant: each node appends to `state.errors` on failure
and the conditional edge after finalize_brief determines overall success.

Checkpointing uses the shared SqliteSaver from memory.database with the
namespaced thread ID:  affiliate:daily:YYYY-MM-DD

Usage:
    from affiliate_factory.graphs.daily_pipeline import build_daily_graph
    from affiliate_factory.graphs import make_thread_id

    graph = build_daily_graph()
    state = DailyPipelineState(date="2026-04-26", niche="ai_side_hustle")
    result = await graph.ainvoke(
        state,
        {"configurable": {"thread_id": make_thread_id("daily", "2026-04-26")}}
    )
"""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from affiliate_factory.graphs import THREAD_NAMESPACE, make_thread_id


# ── State ─────────────────────────────────────────────────────────────────────


class DailyPipelineState(TypedDict):
    """Full mutable state passed between daily pipeline nodes.

    Fields populated progressively as the graph executes.
    All list fields are annotated with operator.add for parallel fan-in merges.
    """

    date: str                          # YYYY-MM-DD — pipeline run date
    niche: str                         # niche_slug from AffiliateSettings
    trends: list[dict[str, Any]]       # output of TrendMinerAgent
    offers: list[dict[str, Any]]       # output of OfferResearchAgent (evaluated)
    competitors: dict[str, Any]        # output of CompetitorScoutAgent
    brief: dict[str, Any] | None       # output of BriefBuilderAgent
    hook_options: list[str]            # output of ScriptForgeAgent
    script: str                        # chosen script text
    visual_prompts: list[dict[str, Any]]  # output of VisualPromptAgent
    captions: dict[str, Any]           # output of CaptionAgent
    status: str                        # pending | running | done | failed
    errors: list[str]                  # accumulated error messages


# ── Node stubs ────────────────────────────────────────────────────────────────


async def node_mine_trends(state: DailyPipelineState) -> dict[str, Any]:
    """Invoke TrendMinerAgent and merge results into state.

    Returns:
        Partial state dict: {"trends": [...], "errors": [...]}
    """
    ...


async def node_research_offers(state: DailyPipelineState) -> dict[str, Any]:
    """Invoke OfferResearchAgent and merge results into state.

    Returns:
        Partial state dict: {"offers": [...], "errors": [...]}
    """
    ...


async def node_scout_competitors(state: DailyPipelineState) -> dict[str, Any]:
    """Invoke CompetitorScoutAgent and merge results into state.

    Returns:
        Partial state dict: {"competitors": {...}, "errors": [...]}
    """
    ...


async def node_build_brief(state: DailyPipelineState) -> dict[str, Any]:
    """Invoke BriefBuilderAgent to synthesise trends + offers + competitors.

    Returns:
        Partial state dict: {"brief": {...}, "errors": [...]}
    """
    ...


async def node_forge_script(state: DailyPipelineState) -> dict[str, Any]:
    """Invoke ScriptForgeAgent to generate hooks and full script.

    Returns:
        Partial state dict: {"hook_options": [...], "script": str, "errors": [...]}
    """
    ...


async def node_generate_visuals(state: DailyPipelineState) -> dict[str, Any]:
    """Invoke VisualPromptAgent to generate scene-by-scene Higgsfield prompts.

    Returns:
        Partial state dict: {"visual_prompts": [...], "errors": [...]}
    """
    ...


async def node_write_captions(state: DailyPipelineState) -> dict[str, Any]:
    """Invoke CaptionAgent to generate multi-platform captions.

    Returns:
        Partial state dict: {"captions": {...}, "errors": [...]}
    """
    ...


async def node_finalize_brief(state: DailyPipelineState) -> dict[str, Any]:
    """Persist the complete brief (script + visuals + captions) to SQLite.

    Updates the `briefs` row status from 'draft' → 'ready'.

    Returns:
        Partial state dict: {"status": "done" | "failed", "errors": [...]}
    """
    ...


def route_after_finalize(state: DailyPipelineState) -> str:
    """Conditional edge: determine terminal node based on pipeline outcome.

    Returns:
        "done" (→ END) if status is 'done', else "failed" (→ END).
    """
    return state.get("status", "failed")


# ── Graph builder ─────────────────────────────────────────────────────────────


def build_daily_graph() -> StateGraph:
    """Assemble and compile the daily pipeline StateGraph.

    Attaches the shared LangGraph SqliteSaver checkpointer so each run
    can be resumed from the last completed node on failure.

    Returns:
        Compiled LangGraph StateGraph ready for ainvoke / invoke.
    """
    ...

"""Affiliate Factory — autonomous TikTok affiliate content pipeline for JAQ-AI.

Produces daily production briefs (script + visual prompts + captions) and
runs weekly performance reviews.  Integrates with the existing JAQ-AI
infrastructure without touching any core files:

  - Agents   → extend agents.base_agent.BaseAgent
  - Memory   → own ChromaDB collection (jaq_affiliate_<niche_slug>)
  - Graphs   → independent LangGraph StateGraphs, thread-namespaced "affiliate:*"
  - Telegram → register_affiliate_commands(app) in bot/telegrambot.py
  - Config   → AffiliateSettings (AFFILIATE_* env vars)

Quick start:
    python affiliate_factory/data/chromadb_init.py   # bootstrap knowledge store
    python affiliate_factory/data/chromadb_init.py --db  # also init SQLite tables
"""

__version__ = "0.1.0"
__all__: list[str] = ["__version__"]

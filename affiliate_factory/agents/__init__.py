"""Affiliate Factory agents package.

Exposes all agent classes and the shared AffiliateBaseAgent base.
Import pattern used by graph nodes:
    from affiliate_factory.agents import BriefBuilderAgent, ScriptForgeAgent
"""

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.agents.brief_builder import BriefBuilderAgent
from affiliate_factory.agents.caption_agent import CaptionAgent
from affiliate_factory.agents.competitor_scout import CompetitorScoutAgent
from affiliate_factory.agents.offer_research import OfferResearchAgent
from affiliate_factory.agents.optimizer import OptimizerAgent
from affiliate_factory.agents.performance_logger import PerformanceLoggerAgent
from affiliate_factory.agents.script_forge import ScriptForgeAgent
from affiliate_factory.agents.trend_miner import TrendMinerAgent
from affiliate_factory.agents.visual_prompt import VisualPromptAgent

__all__ = [
    "AffiliateBaseAgent",
    "TrendMinerAgent",
    "OfferResearchAgent",
    "CompetitorScoutAgent",
    "ScriptForgeAgent",
    "VisualPromptAgent",
    "CaptionAgent",
    "BriefBuilderAgent",
    "PerformanceLoggerAgent",
    "OptimizerAgent",
]

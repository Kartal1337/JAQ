"""OfferResearchAgent — multi-provider affiliate offer discovery and evaluation.

Architecture: Strategy Pattern
  OfferResearchAgent orchestrates one or more OfferProviderStrategy instances.
  Each strategy handles a specific affiliate network (PartnerStack, Impact,
  Rewardful, or a manually curated seed list).

Active strategies (v1):
  - SaaSDirectStrategy  — static curated seed programs, immediately usable
  - PartnerStackStrategy — stub, activate when API access is available

Disabled (removed): ClickBank / Jasper (14-day cookie, weak program)
Active seed programs: Higgsfield, Synthesia, ElevenLabs, Copy.ai

_execute contract (inherited from BaseAgent):
  task (str)    — JSON string with keys: niche_keywords, filters, evaluate
                  fallback: treat as plain niche keyword if not valid JSON
  context (str) — semantic context injected by BaseAgent.run() from ChromaDB
  returns (str) — JSON string: {"offers": [EvaluatedOffer, ...]}
"""

from __future__ import annotations

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage

from affiliate_factory.agents.base import AffiliateBaseAgent
from affiliate_factory.prompts.system_prompts import OFFER_RESEARCH_SYSTEM

logger = logging.getLogger(__name__)


# ── Data transfer objects ─────────────────────────────────────────────────────


@dataclass
class RawOffer:
    """Provider-specific raw data before normalisation.

    Each OfferProviderStrategy.discover() returns a list of these;
    normalize() converts them to the canonical offers-table dict.
    """

    provider: str
    external_id: str
    name: str
    raw_data: dict[str, Any] = field(default_factory=dict)


# ── Strategy interface ────────────────────────────────────────────────────────


class OfferProviderStrategy(ABC):
    """Contract for all affiliate-network provider strategies.

    Subclasses implement two async operations:
      discover()  — fetch raw offer list from the network
      normalize() — convert a RawOffer to the canonical offers-table schema
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier string stored in offers.provider."""
        ...

    @abstractmethod
    async def discover(
        self,
        niche_keywords: list[str],
        filters: dict[str, Any],
    ) -> list[RawOffer]:
        """Return raw offers matching the given niche keywords and filters.

        Args:
            niche_keywords: Lowercase tag strings used to filter offers
                            (e.g. ["ai_video", "creator_economy"]).
            filters:        Additional filter criteria (min_commission_pct, etc.).
                            Strategies are free to ignore unsupported keys.

        Returns:
            List of RawOffer objects (may be empty).
        """
        ...

    @abstractmethod
    async def normalize(self, raw: RawOffer) -> dict[str, Any]:
        """Convert a RawOffer to the canonical offers-table column dict.

        Returns:
            Dict with keys matching the offers table columns (offer_id, provider,
            external_id, name, vendor, category, niche_tags, affiliate_url,
            landing_page_url, commission_model, commission_pct, recurring_months,
            cookie_days, is_anchor_product, raw_metadata).
            Scores (quality_score, ugc_fitness_score) are NOT set here —
            OfferResearchAgent._evaluate_offer() fills them in later.
        """
        ...


# ── Strategy: manually curated SaaS programs ─────────────────────────────────


class SaaSDirectStrategy(OfferProviderStrategy):
    """Manually curated high-quality SaaS affiliate programs.

    The SEED_PROGRAMS list is the single source of truth for v1.
    No external API calls — data is embedded directly.
    Add new programs by appending to SEED_PROGRAMS; the normalise step
    auto-generates offer_id as "direct_saas:{external_id}".

    Excluded programs:
      - Jasper: 14-day cookie (insufficient attribution window)
    """

    provider_name = "direct_saas"

    SEED_PROGRAMS: list[dict[str, Any]] = [
        {
            "external_id": "higgsfield",
            "name": "Higgsfield",
            "vendor": "Higgsfield AI",
            "category": "ai_video",
            "niche_tags": ["ai_video", "cinematic", "viral_effects", "creator_economy"],
            "affiliate_url": "https://higgsfield.ai/ambassador-program",
            "landing_page_url": "https://higgsfield.ai",
            "commission_model": "hybrid_view_plus_referral",
            "commission_pct": 15.0,
            "commission_value_usd": None,
            "recurring_months": 12,
            "cookie_days": None,            # Impact platform — verify exact value
            "is_anchor_product": True,
            "raw_metadata": {
                "tracking_platform": "impact.com",
                "additional_revenue": "view_based_earn_program",
                "earn_caps": {
                    "first_day_usd": 1000,
                    "lifetime_per_video_usd": 2500,
                },
                "earn_supported_platforms": ["instagram", "youtube"],
                "earn_payment_processor": "Garna",
            },
        },
        {
            "external_id": "synthesia",
            "name": "Synthesia",
            "vendor": "Synthesia Ltd",
            "category": "ai_video",
            "niche_tags": ["ai_avatar", "talking_head", "training_video", "course_creator"],
            "affiliate_url": "https://www.synthesia.io/partners/affiliates",
            "landing_page_url": "https://www.synthesia.io",
            "commission_model": "recurring_capped",
            "commission_pct": 25.0,
            "commission_value_usd": None,
            "recurring_months": 12,
            "cookie_days": 60,
            "is_anchor_product": False,
            "raw_metadata": {
                "tracking_platform": "rewardful",
                "min_payout_usd": 30,
                "perks": [
                    "free_starter_after_10_sales",
                    "custom_avatar_after_15_sales",
                ],
                "payment_methods": ["paypal", "bank_transfer"],
            },
        },
        {
            "external_id": "elevenlabs",
            "name": "ElevenLabs",
            "vendor": "ElevenLabs",
            "category": "ai_voice",
            "niche_tags": ["voiceover", "tts", "voice_cloning", "audio_content"],
            "affiliate_url": "https://elevenlabs.io/affiliates",
            "landing_page_url": "https://elevenlabs.io",
            "commission_model": "recurring_capped",
            "commission_pct": 22.0,
            "commission_value_usd": None,
            "recurring_months": 12,
            "cookie_days": 90,
            "is_anchor_product": False,
            "raw_metadata": {
                "tracking_platform": "partnerstack",
                "min_payout_usd": 5,
                "business_tier_commission_pct": 11,
                "payment_methods": ["stripe", "paypal", "wire"],
                "payout_delay_days": 90,  # 3 months after license activation
            },
        },
        {
            "external_id": "copyai",
            "name": "Copy.ai",
            "vendor": "Copy.ai Inc",
            "category": "ai_writing",
            "niche_tags": ["copywriting", "content_creation", "marketing", "ad_copy"],
            "affiliate_url": "https://www.copy.ai/affiliate",
            "landing_page_url": "https://www.copy.ai",
            "commission_model": "recurring_capped",
            "commission_pct": 45.0,
            "commission_value_usd": None,
            "recurring_months": 12,
            "cookie_days": 60,
            "is_anchor_product": False,
            "raw_metadata": {
                "tracking_platform": "direct",
                "avg_plan_price_usd": 49,
                "payment_methods": ["paypal"],
            },
        },
    ]

    async def discover(
        self,
        niche_keywords: list[str],
        filters: dict[str, Any],
    ) -> list[RawOffer]:
        """Return seed programs whose niche_tags overlap with niche_keywords.

        If niche_keywords is empty, all seed programs are returned.
        Applies min_commission_pct filter from `filters` if present.
        """
        kw_set = {k.lower() for k in niche_keywords}
        min_pct = filters.get("min_commission_pct", 0)

        results: list[RawOffer] = []
        for prog in self.SEED_PROGRAMS:
            # Tag-overlap filter (skip only when keywords given and no match)
            if kw_set:
                tag_set = {t.lower() for t in prog["niche_tags"]}
                if not kw_set & tag_set:
                    continue

            # Commission filter
            pct = prog.get("commission_pct") or 0
            if pct < min_pct:
                continue

            results.append(
                RawOffer(
                    provider=self.provider_name,
                    external_id=prog["external_id"],
                    name=prog["name"],
                    raw_data=prog,
                )
            )

        return results

    async def normalize(self, raw: RawOffer) -> dict[str, Any]:
        """Map seed program dict to the canonical offers-table schema."""
        d = raw.raw_data
        return {
            "offer_id": f"{self.provider_name}:{raw.external_id}",
            "provider": self.provider_name,
            "external_id": raw.external_id,
            "name": d["name"],
            "vendor": d.get("vendor"),
            "category": d.get("category"),
            "niche_tags": d.get("niche_tags", []),
            "affiliate_url": d.get("affiliate_url"),
            "landing_page_url": d.get("landing_page_url"),
            "commission_model": d["commission_model"],
            "commission_value_usd": d.get("commission_value_usd"),
            "commission_pct": d.get("commission_pct"),
            "recurring_months": d.get("recurring_months"),
            "cookie_days": d.get("cookie_days"),
            "is_anchor_product": int(bool(d.get("is_anchor_product", False))),
            "raw_metadata": d.get("raw_metadata", {}),
        }


# ── Strategy: PartnerStack (stub) ─────────────────────────────────────────────


class PartnerStackStrategy(OfferProviderStrategy):
    """PartnerStack marketplace integration — activate when API key is available.

    Requires:  AFFILIATE_PARTNERSTACK_API_KEY in .env
    API docs:  https://developers.partnerstack.com/
    """

    provider_name = "partnerstack"

    async def discover(
        self,
        niche_keywords: list[str],
        filters: dict[str, Any],
    ) -> list[RawOffer]:
        raise NotImplementedError("PartnerStack API integration pending.")

    async def normalize(self, raw: RawOffer) -> dict[str, Any]:
        raise NotImplementedError


# ── Agent ─────────────────────────────────────────────────────────────────────


class OfferResearchAgent(AffiliateBaseAgent):
    """Discovers, evaluates, and persists affiliate offers from multiple providers.

    Orchestration flow:
      1. Each active strategy runs discover() → list[RawOffer]
      2. Each RawOffer is passed through normalize() → canonical dict
      3. If evaluate=True, Claude scores each offer (quality + UGC fitness + hook angles)
      4. Qualifying offers (quality_score >= 6) are stored as passages in ChromaDB
      5. All offers are upserted to the SQLite offers table
      6. Returns JSON string {"offers": [...]}

    Strategies that raise NotImplementedError are silently skipped so adding
    a new stub strategy never breaks the active pipeline.
    """

    name = "OfferResearchAgent"
    _base_system_prompt = OFFER_RESEARCH_SYSTEM
    tools = []  # Tavily added per-strategy when web scraping is needed

    def __init__(self, skill_name: str | None = None) -> None:
        super().__init__(skill_name=skill_name)
        self.strategies: list[OfferProviderStrategy] = [
            SaaSDirectStrategy(),
            # PartnerStackStrategy(),  # uncomment when API key is available
        ]

    # ── BaseAgent contract ────────────────────────────────────────────────────

    async def _execute(self, task: str, context: str) -> str:
        """Discover, evaluate, and persist offers.

        Args:
            task:    JSON string with keys:
                       niche_keywords (list[str])  — tag overlap filter
                       filters        (dict)        — min_commission_pct, etc.
                       evaluate       (bool)        — run Claude scoring (default True)
                     Falls back to treating task as a bare niche keyword string.
            context: Semantic context injected by BaseAgent.run() (ChromaDB).

        Returns:
            JSON string: {"offers": [evaluated offer dicts sorted by quality_score desc]}
        """
        try:
            task_dict: dict[str, Any] = json.loads(task)
        except (json.JSONDecodeError, TypeError):
            task_dict = {"niche_keywords": [task], "filters": {}, "evaluate": True}

        niche_keywords: list[str] = task_dict.get("niche_keywords", [])
        filters: dict[str, Any] = task_dict.get("filters", {})
        should_evaluate: bool = task_dict.get("evaluate", True)

        # 1. Collect raw offers from all active strategies
        all_offers: list[dict[str, Any]] = []
        for strategy in self.strategies:
            try:
                raws = await strategy.discover(niche_keywords, filters)
                for raw in raws:
                    normalized = await strategy.normalize(raw)
                    all_offers.append(normalized)
            except NotImplementedError:
                logger.debug("Strategy %s not implemented — skipping.", strategy.provider_name)
                continue
            except Exception as exc:
                logger.warning("Strategy %s failed: %s", strategy.provider_name, exc)
                continue

        # 2. Score each offer with Claude
        if should_evaluate:
            for offer in all_offers:
                eval_result = await self._evaluate_offer(offer)
                offer["quality_score"] = eval_result["quality_score"]
                offer["ugc_fitness_score"] = eval_result["ugc_fitness_score"]
                offer["hook_angles"] = eval_result["hook_angles"]

        # 3. Persist to SQLite (all offers, scored or not)
        await self._persist_offers(all_offers)

        # 4. Store high-quality offers in ChromaDB for downstream retrieval
        for offer in all_offers:
            if (offer.get("quality_score") or 0) >= 6:
                await self.store_passage(
                    text=self._offer_to_passage(offer),
                    metadata={
                        "offer_id": offer["offer_id"],
                        "category": offer.get("category", ""),
                        "is_anchor": bool(offer.get("is_anchor_product", False)),
                        "type": "offer",
                    },
                )

        # Sort by quality_score descending (None scores sort to bottom)
        all_offers.sort(key=lambda o: o.get("quality_score") or 0, reverse=True)

        return json.dumps({"offers": all_offers}, ensure_ascii=False, default=str)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _evaluate_offer(self, offer: dict[str, Any]) -> dict[str, Any]:
        """Ask Claude to score an offer for TikTok/IG faceless content fitness.

        Returns:
            Dict with keys: quality_score (float 0-10), ugc_fitness_score (float 0-10),
            hook_angles (list[str] with 3 items).
            Falls back to neutral scores on any parse error.
        """
        _FALLBACK = {
            "quality_score": 5.0,
            "ugc_fitness_score": 5.0,
            "hook_angles": ["needs manual review"],
        }

        prompt = f"""Aşağıdaki SaaS affiliate ürününü TikTok ve Instagram'da faceless \
content üretmek için değerlendir.

Ürün: {offer['name']}
Kategori: {offer.get('category', 'bilinmiyor')}
Komisyon: %{offer.get('commission_pct')} — {offer.get('recurring_months')} ay recurring
Cookie süresi: {offer.get('cookie_days')} gün
Detaylar: {json.dumps(offer.get('raw_metadata', {}), ensure_ascii=False)}

Sadece aşağıdaki JSON formatında yanıt ver, başka metin ekleme:
{{
  "quality_score": <float 0-10>,
  "ugc_fitness_score": <float 0-10>,
  "hook_angles": [
    "<1. cümle — bir hook açısı>",
    "<2. cümle — farklı bir açı>",
    "<3. cümle — üçüncü açı>"
  ],
  "reasoning": "<kısa neden, 1 cümle>"
}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            raw_content: str = response.content.strip()

            # Strip markdown code fences if present
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]

            parsed = json.loads(raw_content)
            return {
                "quality_score": float(parsed.get("quality_score", 5.0)),
                "ugc_fitness_score": float(parsed.get("ugc_fitness_score", 5.0)),
                "hook_angles": parsed.get("hook_angles", _FALLBACK["hook_angles"]),
            }
        except Exception as exc:
            logger.warning(
                "Offer evaluation failed for %s: %s — using fallback scores.",
                offer.get("name"),
                exc,
            )
            return _FALLBACK

    async def _persist_offers(self, offers: list[dict[str, Any]]) -> None:
        """Upsert all offers into the SQLite affiliate.db offers table.

        Uses INSERT OR REPLACE so re-running the pipeline is idempotent.
        raw_metadata and niche_tags are serialised to JSON strings.
        """
        from affiliate_factory.config import get_affiliate_settings

        db_path = get_affiliate_settings().db_path
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            for offer in offers:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO offers (
                        offer_id, provider, external_id, name, vendor,
                        category, niche_tags, affiliate_url, landing_page_url,
                        commission_model, commission_value_usd, commission_pct,
                        recurring_months, cookie_days,
                        quality_score, ugc_fitness_score, is_anchor_product,
                        raw_metadata, researched_at, last_evaluated_at, is_active
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, 1
                    )
                    """,
                    (
                        offer["offer_id"],
                        offer["provider"],
                        offer["external_id"],
                        offer["name"],
                        offer.get("vendor"),
                        offer.get("category"),
                        json.dumps(offer.get("niche_tags", []), ensure_ascii=False),
                        offer.get("affiliate_url"),
                        offer.get("landing_page_url"),
                        offer["commission_model"],
                        offer.get("commission_value_usd"),
                        offer.get("commission_pct"),
                        offer.get("recurring_months"),
                        offer.get("cookie_days"),
                        offer.get("quality_score"),
                        offer.get("ugc_fitness_score"),
                        offer.get("is_anchor_product", 0),
                        json.dumps(offer.get("raw_metadata", {}), ensure_ascii=False),
                        now,
                        now if offer.get("quality_score") is not None else None,
                    ),
                )
            conn.commit()
            logger.info("Persisted %d offer(s) to %s.", len(offers), db_path)
        finally:
            conn.close()

    @staticmethod
    def _offer_to_passage(offer: dict[str, Any]) -> str:
        """Build a ChromaDB passage string for an offer.

        The 'passage: ' prefix is added automatically by store_passage().
        Includes the Claude-generated hook_angles so ScriptForgeAgent can
        retrieve ready-made angle ideas from ChromaDB context.
        """
        hooks = " | ".join(offer.get("hook_angles", []))
        return (
            f"{offer['name']} — {offer.get('category', '')} affiliate program. "
            f"Vendor: {offer.get('vendor', '')}. "
            f"Commission: {offer.get('commission_pct')}% recurring "
            f"{offer.get('recurring_months')} months, "
            f"{offer.get('cookie_days')}-day cookie. "
            f"Quality: {offer.get('quality_score')}/10, "
            f"UGC fitness: {offer.get('ugc_fitness_score')}/10. "
            f"Niche tags: {', '.join(offer.get('niche_tags', []))}. "
            f"Hook angles: {hooks}."
        )


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    async def _main() -> None:
        agent = OfferResearchAgent()
        result = await agent.run(
            task=json.dumps({
                "niche_keywords": ["ai_video", "creator_economy", "ai_writing"],
                "filters": {"min_commission_pct": 15},
                "evaluate": True,
            }),
            chat_id=0,
        )

        if not result.success:
            print(f"[ERROR] {result.error}")
            return

        data = json.loads(result.output)
        for offer in data["offers"]:
            print(
                f"\n{offer['name']}"
                f"\n  quality={offer.get('quality_score'):.1f}  "
                f"ugc={offer.get('ugc_fitness_score'):.1f}  "
                f"anchor={bool(offer.get('is_anchor_product'))}"
            )
            for i, angle in enumerate(offer.get("hook_angles", []), 1):
                print(f"  hook {i}: {angle}")

    asyncio.run(_main())

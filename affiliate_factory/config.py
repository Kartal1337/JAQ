"""AffiliateSettings — Pydantic v2 settings for the affiliate_factory module.

All fields are read from the .env file using the AFFILIATE_ prefix so they
never collide with the core JAQ-AI settings (ANTHROPIC_API_KEY etc.).

Example .env additions:
    AFFILIATE_NICHE_SLUG=ai_side_hustle
    AFFILIATE_DB_PATH=./data/affiliate.db
    AFFILIATE_CLICKBANK_API_KEY=...
    AFFILIATE_HIGGSFIELD_API_KEY=...
    AFFILIATE_TIKTOK_ACCOUNT_HANDLE=@yourhandle
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AffiliateSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AFFILIATE_",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Niche identity ──────────────────────────────────────────────────────
    NICHE_COLLECTION_TEMPLATE: str = "jaq_affiliate_{niche_slug}"
    niche_slug: str = Field(
        default="ai_side_hustle",
        description="Snake-case identifier used in ChromaDB collection name and SQLite records.",
    )

    @property
    def chroma_collection_name(self) -> str:
        """Derived ChromaDB collection name for this niche."""
        return self.NICHE_COLLECTION_TEMPLATE.format(niche_slug=self.niche_slug)

    # ── Storage ─────────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(
        default="./data/chroma_db",
        description="Must match core JAQ-AI chroma_persist_dir so a single ChromaDB instance is shared.",
    )
    db_path: str = Field(
        default="./data/affiliate.db",
        description="SQLite database for offers, briefs, videos, performance, and winners_pattern.",
    )

    # ── External APIs ────────────────────────────────────────────────────────
    clickbank_api_key: str = Field(
        default="",
        description="ClickBank REST API key for offer research.",
    )
    clickbank_clerk_id: str = Field(
        default="",
        description="ClickBank clerk / account ID.",
    )
    higgsfield_api_key: str = Field(
        default="",
        description="Higgsfield AI API key for video generation.",
    )
    tiktok_account_handle: str = Field(
        default="",
        description="TikTok posting account handle (e.g. @myaccount).",
    )

    # ── Offer research ───────────────────────────────────────────────────────
    min_gravity_score: float = Field(
        default=20.0,
        ge=0.0,
        description="ClickBank gravity threshold; offers below this are skipped.",
    )
    max_offers_per_run: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of offers to evaluate in one daily pipeline run.",
    )

    # ── Script generation ────────────────────────────────────────────────────
    target_script_words: int = Field(
        default=150,
        ge=50,
        le=500,
        description="Target word count for TikTok video scripts.",
    )
    hook_variants_per_brief: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of alternative hooks to generate per brief.",
    )

    # ── Pipeline scheduling (informational — used by scheduler/cron) ─────────
    daily_pipeline_cron: str = Field(
        default="0 8 * * *",
        description="Cron expression for daily pipeline trigger.",
    )
    weekly_review_cron: str = Field(
        default="0 9 * * 1",
        description="Cron expression for weekly review trigger (Monday 09:00).",
    )


@lru_cache(maxsize=1)
def get_affiliate_settings() -> AffiliateSettings:
    """Return the module-level settings singleton (loaded once per process)."""
    return AffiliateSettings()

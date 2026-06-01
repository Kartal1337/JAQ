# config/settings.py
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    JAQ-AI v2.0 — Merkezi Konfigürasyon
    API key'ler SecretStr ile korunur — loglarda/traceback'lerde maskelenir.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Anthropic ──────────────────────────────────────────────────────────
    anthropic_api_key: SecretStr = Field(..., description="Anthropic Claude API key")
    model_name: str = Field(default="claude-sonnet-4-6")
    model_temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    model_max_tokens: int = Field(default=8192, gt=0)

    # ── Tavily ─────────────────────────────────────────────────────────────
    tavily_api_key: SecretStr = Field(..., description="Tavily web search API key")
    tavily_max_results: int = Field(default=6, ge=1, le=20)

    # ── Telegram ───────────────────────────────────────────────────────────
    telegram_bot_token: SecretStr = Field(..., description="Telegram Bot Token")
    telegram_chat_id: int = Field(..., description="İzin verilen Telegram Chat ID")

    # ── ChromaDB ───────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(default="./data/chroma_db")
    chroma_collection_prefix: str = Field(default="jaq_user")
    memory_history_limit: int = Field(default=10)

    # ── LangGraph Checkpointing ────────────────────────────────────────────
    checkpoint_db_path: str = Field(default="./data/checkpoints.db")

    # ── Uygulama ───────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./data/logs/jaq.log")
    debug_mode: bool = Field(default=False)
    agent_timeout_seconds: int = Field(default=60)

    # ── Rate Limiting ───────────────────────────────────────────────────────
    rate_limit_requests: int = Field(default=20, description="Pencere başına max istek")
    rate_limit_window_seconds: int = Field(default=3600, description="Pencere süresi (saniye)")
    rate_limit_burst: int = Field(default=5, description="Ani yığılmaya izin verilen max istek")

    # ── Input Validation ───────────────────────────────────────────────────
    max_input_length: int = Field(default=4000, description="Kullanıcı girdisi max karakter")
    min_input_length: int = Field(default=2, description="Kullanıcı girdisi min karakter")

    # ── Validators ─────────────────────────────────────────────────────────
    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        if not str(v).startswith("sk-ant-"):
            raise ValueError("Geçersiz Anthropic API key (sk-ant- ile başlamalı)")
        return v

    @field_validator("telegram_bot_token", mode="before")
    @classmethod
    def validate_telegram_token(cls, v: str) -> str:
        if ":" not in str(v):
            raise ValueError("Geçersiz Telegram Bot Token formatı")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level şunlardan biri olmalı: {allowed}")
        return upper

    def get_chroma_collection_name(self, chat_id: int) -> str:
        return f"{self.chroma_collection_prefix}_{chat_id}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

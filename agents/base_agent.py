# agents/base_agent.py
"""
JAQ-AI v2.0 — Tüm Agent'ların Temel Sınıfı

Her departman agent'ı bu sınıftan türer. Şunları garanti altına alır:
  - Tek tip LLM başlatma (Settings'ten, SecretStr ile)
  - Standart AgentResult dönüş formatı
  - Semantik hafıza inject (context otomatik çekilir)
  - Retry mekanizması (tenacity, 3 deneme)
  - Hata yakalama — agent patlarsa sistem durmuyor
  - tools listesi: alt sınıf kendi araçlarını tanımlar
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from anthropic import APIError, APITimeoutError

from config.settings import get_settings
from memory.database import get_memory_manager

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Dönüş Tipi ────────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """
    Tüm agent'ların run() metodundan döndürdüğü standart sonuç.

    Alanlar:
        output      — Kullanıcıya gösterilecek Markdown metin
        agent_name  — Hangi agent ürettiği (loglama + Telegram header için)
        success     — True: başarılı, False: hata var
        error       — Hata mesajı (success=False ise dolu)
        metadata    — Agent'a özgü ek veri (kullanılan tool'lar, kaynak URL'ler vb.)
        duration_s  — Kaç saniye sürdü
    """
    output: str
    agent_name: str
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_s: float = 0.0

    def to_telegram_text(self) -> str:
        """Telegram mesajı için hazır metin."""
        if not self.success:
            return f"⚠️ *{self.agent_name}* bir hatayla karşılaştı:\n`{self.error}`"
        header = f"🤖 *{self.agent_name}*\n{'─' * 30}\n"
        return header + self.output


# ── Temel Sınıf ───────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Tüm JAQ departman agent'larının soyut temel sınıfı.

    Alt sınıf zorunluluğu:
        name         : str            — "ResearchAgent" gibi sabit isim
        system_prompt: str            — config/prompts.py'den alınan prompt
        tools        : list[BaseTool] — agent'ın kullanabileceği araçlar

        _execute(task, context) → str — gerçek iş burada yapılır

    Kullanım:
        class ResearchAgent(BaseAgent):
            name = "ResearchAgent"
            system_prompt = RESEARCH_PROMPT
            tools = [tavily_tool]

            async def _execute(self, task: str, context: str) -> str:
                ...

        result = await ResearchAgent().run(task="...", chat_id=123)
    """

    name: str = "BaseAgent"
    _base_system_prompt: str = ""
    tools: list[BaseTool] = []

    def __init__(self, skill_name: str | None = None) -> None:
        self._llm: ChatAnthropic | None = None
        self.skill_name = skill_name
        self._skill = None
        if skill_name:
            from core.skill_loader import get_registry  # lazy — circular import'u önler
            self._skill = get_registry().get(skill_name)
            if self._skill is None:
                logger.warning(f"{self.name}: '{skill_name}' skill bulunamadı")

    @property
    def system_prompt(self) -> str:
        prompt = self._base_system_prompt
        if self._skill:
            prompt += "\n\n---\n\n" + self._skill.as_prompt_block(include_files=True)
        return prompt

    # ── LLM (lazy, singleton per instance) ───────────────────────────────

    @property
    def llm(self) -> ChatAnthropic:
        """LLM ilk kullanımda oluşturulur (module-level değil)."""
        if self._llm is None:
            self._llm = ChatAnthropic(
                model=settings.model_name,
                api_key=settings.anthropic_api_key.get_secret_value(),
                temperature=settings.model_temperature,
                max_tokens=settings.model_max_tokens,
            )
        return self._llm

    # ── Alt Sınıfın Implement Edeceği Metot ──────────────────────────────

    @abstractmethod
    async def _execute(self, task: str, context: str) -> str:
        """
        Gerçek agent mantığı buraya gelir.

        Args:
            task    : Orchestrator'dan gelen net görev metni
            context : ChromaDB'den çekilen semantik geçmiş bağlam

        Returns:
            Kullanıcıya gösterilecek ham Markdown string
        """

    # ── Public API ────────────────────────────────────────────────────────

    async def run(
        self,
        task: str,
        chat_id: int = 0,
        extra_context: str = "",
    ) -> AgentResult:
        """
        Orchestrator'ın çağırdığı tek metot.

        1. ChromaDB'den semantik bağlam çeker
        2. _execute() çağırır (retry ile)
        3. AgentResult olarak paketler
        4. Hata varsa success=False ile döner (sistem çökmez)
        """
        start = time.monotonic()
        context = extra_context

        if chat_id:
            try:
                memory = get_memory_manager(chat_id)
                semantic_ctx = memory.get_relevant_context(task, k=3)
                if semantic_ctx:
                    context = f"{semantic_ctx}\n{extra_context}".strip()
            except Exception as e:
                logger.warning(f"{self.name}: hafıza bağlamı alınamadı → {e}")

        try:
            output = await self._execute_with_retry(task=task, context=context)
            duration = time.monotonic() - start
            logger.info(f"{self.name} tamamlandı ({duration:.1f}s)")
            return AgentResult(
                output=output,
                agent_name=self.name,
                success=True,
                duration_s=round(duration, 2),
            )
        except Exception as e:
            duration = time.monotonic() - start
            logger.error(f"{self.name} hatası ({duration:.1f}s): {e}", exc_info=True)
            return AgentResult(
                output="",
                agent_name=self.name,
                success=False,
                error=str(e),
                duration_s=round(duration, 2),
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, APITimeoutError)),
        reraise=True,
    )
    async def _execute_with_retry(self, task: str, context: str) -> str:
        """tenacity ile 3 deneme, exponential backoff (2s → 4s → 8s)."""
        return await self._execute(task=task, context=context)

    # ── Yardımcı ──────────────────────────────────────────────────────────

    def _build_prompt(self, task: str, context: str) -> str:
        """
        system_prompt + context + task'ı birleştirerek hazır prompt döner.
        Tüm alt sınıflar _execute() içinde bunu kullanabilir.
        """
        parts = [self.system_prompt.format(task=task)]
        if context:
            parts.insert(0, f"## İlgili Geçmiş Bağlam\n{context}\n")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"<{self.name} tools={[t.name for t in self.tools]}>"

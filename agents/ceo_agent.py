# agents/ceo_agent.py
"""
JAQ-AI v2.0 — CEO Agent (Geriye Dönük Uyumluluk Wrapper'ı)

Routing mantığı tamamen core/orchestrator.py içindeki supervisor_node'a taşındı.
Bu sınıf eski kodu kırmamak için korunuyor.

Yeni kod: doğrudan orchestrator.process_message() kullanın.
"""

import asyncio
import logging
import warnings

from core.orchestrator import process_message

logger = logging.getLogger(__name__)


class CEOAgent:
    """
    Deprecated: Routing artık LangGraph supervisor_node tarafından yapılıyor.
    Bu sınıf yalnızca eski entegrasyonlar için bırakıldı.
    """

    def decide(self, user_input: str, chat_id: int = 0) -> dict:
        warnings.warn(
            "CEOAgent.decide() deprecated. Kullanın: await orchestrator.process_message()",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(process_message(chat_id, user_input))
            return {"next_agent": "END", "response": response, "reason": "orchestrator"}
        except Exception as e:
            logger.error(f"CEOAgent.decide hatası: {e}")
            return {"next_agent": "END", "response": "", "reason": str(e)}

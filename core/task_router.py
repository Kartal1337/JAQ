# core/task_router.py
"""
JAQ-AI v2.0 — Geriye Dönük Uyumluluk Wrapper'ı

Eski kod (jaq_brain.py) decide_next_agent() fonksiyonunu çağırıyordu.
Bu modül o arayüzü korur, gerçek işi orchestrator'a devreder.

Yeni kod doğrudan orchestrator.process_message() kullanmalı.
"""

import asyncio
import logging

from core.orchestrator import process_message

logger = logging.getLogger(__name__)

# Dummy chat_id — sadece eski kod akışı için, hafıza izolasyonu olmaz
_LEGACY_CHAT_ID = 0


def decide_next_agent(user_input: str) -> dict:
    """
    Eski arayüz: senkron, dict döner.
    Yeni orchestrator async olduğu için event loop içinde çalıştırılır.

    Dönüş formatı (eski jaq_brain.py ile uyumlu):
        {"next": "ResearchAgent", "task": "...", "reason": "..."}
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Zaten async context içindeyse (örn. Telegram handler) uyarı ver
            logger.warning(
                "decide_next_agent() async context içinde çağrıldı. "
                "Doğrudan await process_message() kullanın."
            )
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, process_message(_LEGACY_CHAT_ID, user_input))
                response_text = future.result(timeout=60)
        else:
            response_text = loop.run_until_complete(
                process_message(_LEGACY_CHAT_ID, user_input)
            )
        return {"next": "END", "task": user_input, "reason": "orchestrator yanıtladı", "response": response_text}
    except Exception as e:
        logger.error(f"task_router hatası: {e}")
        return {"next": "END", "task": "", "reason": str(e), "response": ""}

# main.py — JAQ-AI v2.0 Giriş Noktası
"""
Çalıştır:
    python main.py          → FastAPI dashboard (http://localhost:8000)
    python main.py --bot    → Sadece Telegram botu

data/ dizinleri yoksa otomatik oluşturulur.
.env dosyasının proje kökünde olduğundan emin ol.
"""

import logging
import sys
from pathlib import Path


def _bootstrap() -> None:
    for d in ["data/chroma_db", "data/logs"]:
        Path(d).mkdir(parents=True, exist_ok=True)


def _setup_logging(log_file: str, log_level: str) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    except Exception:
        pass
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        level=getattr(logging, log_level, logging.INFO),
        handlers=handlers,
    )


def main() -> None:
    _bootstrap()

    try:
        from config.settings import get_settings
        settings = get_settings()
    except Exception as e:
        print(f"[HATA] Konfigürasyon yüklenemedi: {e}")
        print("  → .env dosyasını kontrol et (.env.example'a bak)")
        sys.exit(1)

    _setup_logging(settings.log_file, settings.log_level)
    logger = logging.getLogger("jaq.main")
    logger.info("=" * 50)
    logger.info("JAQ-AI v2.0 başlatılıyor")
    logger.info(f"Model : {settings.model_name}")
    logger.info("=" * 50)

    if "--bot" in sys.argv:
        # Telegram botu modu
        logger.info("Mod: Telegram Bot")
        from bot.telegrambot import main as bot_main
        bot_main()
    else:
        # Dashboard modu (varsayılan)
        import uvicorn
        logger.info("Mod: FastAPI Dashboard → http://localhost:8000")
        uvicorn.run(
            "api.server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level=settings.log_level.lower(),
        )


if __name__ == "__main__":
    main()

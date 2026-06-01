# JAQ-AI v2.0 — CLAUDE.md

## Proje Özeti

JAQ-AI, LangGraph tabanlı hiyerarşik multi-agent AI sistemi. Bir CEO agent kullanıcı isteğini analiz eder ve doğru özel agent'a yönlendirir. Telegram botu veya FastAPI dashboard olarak çalışır. **ForgeApp** ürünü için geliştirilmektedir.

## Çalıştırma

```bash
# Ortam kur
pip install -r requirements.txt

# .env oluştur
cp .env.example .env

# Dashboard modu (varsayılan) — http://localhost:8000
python main.py

# Telegram bot modu
python main.py --bot

# Testler
pytest tests/
```

## Mimari Katmanlar

```
bot/ veya api/          →  Giriş (Telegram | FastAPI)
core/orchestrator.py    →  LangGraph state machine (CEO routing)
agents/                 →  Özel agent'lar (Research/Writer/Code/Market)
memory/database.py      →  Hibrit bellek (SQLite checkpoint + ChromaDB)
tools/                  →  Paylaşılan araçlar (Tavily search)
config/                 →  Settings (Pydantic) + system promptlar
skills/                 →  Runtime'da yüklenen dinamik beceri modülleri
affiliate_factory/      →  Bağımsız TikTok affiliate pipeline (core'a dokunmaz)
```

## Agent Sistemi

| Agent | Sınıf | Trigger keyword'ler |
|-------|-------|---------------------|
| ResearchAgent | `agents/research_agent.py` | araştır, bul, haberleri, trend |
| WriterAgent | `agents/writer_agent.py` | yaz, içerik, blog, LinkedIn, email |
| CodeAgent | `agents/code_agent.py` | kod, debug, refactor, review |
| MarketAnalysisAgent | `agents/market_analysis_agent.py` | pazar, rekabet, analiz, startup |
| DIRECT | orchestrator supervisor | basit sohbet, soru-cevap |

Tüm agent'lar `BaseAgent`'tan türer (`agents/base_agent.py`). `AgentResult` dataclass döner.

## LangGraph State Akışı

```
START → supervisor_node (CEODecision: next_agent + task + reason)
      → route_after_supervisor (conditional edge)
      → [research|writer|market|code|direct]_node
      → END
```

`JAQState` (TypedDict): `messages`, `chat_id`, `user_input`, `history_summary`, `next_agent`, `task`, `reason`, `agent_output`, `final_response`, `error`

## Bellek Sistemi

- **SQLite SqliteSaver** → LangGraph checkpoint, `./data/checkpoints.db`
- **ChromaDB** → Kullanıcı başına semantik vektör hafızası, `./data/chroma_db/`
- Embedding: `intfloat/multilingual-e5-large-instruct`
- `get_memory_manager(chat_id)` → per-user singleton

> **Gelecek plan:** Supabase + pgvector ile SQLite ve ChromaDB'nin değiştirilmesi (ForgeApp multi-user desteği için)

## Zorunlu .env Değişkenleri

```
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Tüm API key'ler `SecretStr` ile saklanır, loglarda görünmez.

## Önemli Dosyalar

| Dosya | Ne Yapar |
|-------|----------|
| `core/orchestrator.py` | Tüm sistemin kalbi — değiştirilirken dikkat |
| `config/prompts.py` | Agent system promptları — davranış buradan ayarlanır |
| `config/settings.py` | Pydantic settings, yeni env değişkeni buraya eklenir |
| `memory/database.py` | MemoryManager + checkpointer — bellek değişikliği buradan |
| `bot/telegrambot.py` | Telegram komutları ve handler'lar |
| `affiliate_factory/` | Bağımsız subsystem — core dosyalara dokunmaz |

## Güvenlik ve Sınırlar

- Tek kullanıcı auth: `settings.telegram_chat_id` ile Telegram'da gate
- Rate limit: saatte 20 istek, 5 burst (`core/rate_limiter.py`)
- Input validation: max 4000 karakter, prompt injection koruması (`core/input_validator.py`)
- Agent timeout: 60 saniye (ayarlanabilir)

## Test Komutu

```bash
pytest tests/ -v
pytest tests/test_input_validator.py  # Spesifik
```

## Kullanılan Teknolojiler

- **LLM**: Claude Sonnet 4.6 (Anthropic)
- **Orchestration**: LangGraph v1.1+
- **Memory**: ChromaDB + LangGraph SqliteSaver
- **Search**: Tavily API
- **Bot**: python-telegram-bot v22
- **Web**: FastAPI + Uvicorn
- **Config**: Pydantic v2 + pydantic-settings

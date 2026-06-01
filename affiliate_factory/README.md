# Affiliate Factory

Autonomous TikTok affiliate content pipeline for JAQ-AI.

Produces daily production briefs (script + visual prompts + captions) and weekly performance reviews without touching any core JAQ-AI files.

---

## Module structure

```
affiliate_factory/
├── config.py                  # AffiliateSettings (AFFILIATE_* env vars)
├── agents/                    # AffiliateBaseAgent + 9 specialist agents
├── graphs/                    # LangGraph daily_pipeline + weekly_review
├── prompts/                   # System prompts, hook formulas, visual templates
├── data/
│   ├── schema.sql             # SQLite table definitions
│   └── chromadb_init.py       # Bootstrap script
└── telegram_commands.py       # 6 Telegram commands
```

---

## Prerequisites

1. Existing JAQ-AI `.env` must already contain the core variables (`ANTHROPIC_API_KEY`, `CHROMA_PERSIST_DIR`, `CHECKPOINT_DB_PATH`, etc.).
2. Add the affiliate-specific variables listed below.
3. Run the bootstrap script once.

---

## .env additions

```dotenv
# ── Affiliate Factory ────────────────────────────────────────────────────────
AFFILIATE_NICHE_SLUG=ai_side_hustle          # snake_case; becomes ChromaDB collection suffix
AFFILIATE_DB_PATH=./data/affiliate.db        # separate SQLite file from checkpoints.db

# ClickBank (offer research)
AFFILIATE_CLICKBANK_API_KEY=
AFFILIATE_CLICKBANK_CLERK_ID=

# Higgsfield AI (visual prompt generation)
AFFILIATE_HIGGSFIELD_API_KEY=

# TikTok posting account
AFFILIATE_TIKTOK_ACCOUNT_HANDLE=@yourhandle

# Offer filtering
AFFILIATE_MIN_GRAVITY_SCORE=20.0
AFFILIATE_MAX_OFFERS_PER_RUN=10

# Script generation
AFFILIATE_TARGET_SCRIPT_WORDS=150
AFFILIATE_HOOK_VARIANTS_PER_BRIEF=3

# Pipeline scheduling (informational — used by cron/scheduler)
AFFILIATE_DAILY_PIPELINE_CRON=0 8 * * *
AFFILIATE_WEEKLY_REVIEW_CRON=0 9 * * 1
```

---

## Bootstrap (run once)

```bash
# 1. Install no new packages — affiliate_factory reuses JAQ-AI dependencies.
#    Verify requirements: langchain, langgraph, chromadb, sentence-transformers,
#    sqlite3 (stdlib), python-telegram-bot are all present.

# 2. Initialise ChromaDB collection + SQLite tables:
python affiliate_factory/data/chromadb_init.py --db

# Expected output:
# INFO  ChromaDB collection ready: jaq_affiliate_ai_side_hustle
# INFO  SQLite database ready: data/affiliate.db
# INFO  affiliate_factory storage bootstrap complete.
```

---

## Integration with JAQ-AI

### 1. Register Telegram commands

In [bot/telegrambot.py](../bot/telegrambot.py), inside `build_application()`, add **one line** after the existing `app.add_handler()` calls:

```python
from affiliate_factory.telegram_commands import register_affiliate_commands

def build_application() -> Application:
    app = Application.builder().token(...).post_init(_post_init).build()

    # ... existing core handlers ...

    register_affiliate_commands(app)  # ← add this line
    return app
```

This registers 6 commands: `/affiliate`, `/affiliate_run`, `/affiliate_log`, `/affiliate_stats`, `/affiliate_weekly`, `/affiliate_winner`.

### 2. (Optional) Update Telegram command menu

In `_post_init`, append the new commands to `set_my_commands`:

```python
await application.bot.set_my_commands([
    # ... existing entries ...
    ("affiliate",        "Bugünün brief durumu"),
    ("affiliate_run",    "Günlük pipeline'ı tetikle"),
    ("affiliate_log",    "Video metriği kaydet"),
    ("affiliate_stats",  "7 günlük performans özeti"),
    ("affiliate_weekly", "Haftalık review raporu"),
    ("affiliate_winner", "Kazanan pattern'leri göster"),
])
```

---

## Daily usage flow

```
09:00  Daily pipeline runs automatically (or /affiliate_run)
         → TrendMinerAgent    finds today's angle
         → OfferResearchAgent evaluates offers
         → CompetitorScoutAgent spots competitor hooks
         → BriefBuilderAgent   builds the brief
         → ScriptForgeAgent    writes the script
         → VisualPromptAgent   generates Higgsfield prompts
         → CaptionAgent        writes captions
         → Brief saved to SQLite with status='ready'

/affiliate          → review the brief
                      copy script + visual prompts → Higgsfield → post to TikTok

/affiliate_log {"video_id":"...", "tiktok_url":"...", "views":0}
                    → register the posted video

(next day or on demand)
/affiliate_log {"video_id":"...", "views":15000, "likes":800, ...}
                    → log updated metrics

Monday 09:00  Weekly review runs automatically (or /affiliate_weekly --run)
                    → OptimizerAgent extracts winning patterns
                    → Patterns saved to SQLite + ChromaDB
                    → Report sent to Telegram
```

---

## ChromaDB collection

- **Name**: `jaq_affiliate_{AFFILIATE_NICHE_SLUG}` (e.g. `jaq_affiliate_ai_side_hustle`)
- **Directory**: same as core JAQ-AI (`CHROMA_PERSIST_DIR=./data/chroma_db`)
- **Embedding model**: `intfloat/multilingual-e5-large-instruct` (shared with core)
- **Prefix convention**: `passage: ...` for writes, `query: ...` for searches

---

## SQLite database

- **File**: `AFFILIATE_DB_PATH` (default `./data/affiliate.db`)
- **Tables**: `offers`, `briefs`, `videos`, `performance`, `winners_pattern`
- **Schema**: [data/schema.sql](data/schema.sql)
- **Migration**: none — all tables use `CREATE TABLE IF NOT EXISTS`

---

## Thread ID namespacing

LangGraph checkpoints use the `affiliate:` namespace to avoid collision with the main orchestrator:

```
affiliate:daily:2026-04-26    ← daily pipeline for April 26
affiliate:weekly:2026-W17     ← weekly review for week 17
```

Core orchestrator uses plain integer chat IDs (e.g. `"987654321"`) — no overlap is possible.

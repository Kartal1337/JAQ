"""Telegram command handlers for the affiliate_factory module.

Integration — add ONE line to bot/telegrambot.py:

    # In build_application(), after the existing app.add_handler() calls:
    from affiliate_factory.telegram_commands import register_affiliate_commands
    register_affiliate_commands(app)

Commands registered:
    /affiliate        — today's brief status (draft / ready / posted)
    /affiliate_run    — manually trigger the daily pipeline for today
    /affiliate_log    — log video performance metrics (accepts JSON or plain text)
    /affiliate_stats  — show 7-day performance summary table
    /affiliate_weekly — trigger or view latest weekly review report
    /affiliate_winner — show current winners_pattern entries from SQLite
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


# ── Authorization helper (mirrors bot/telegrambot.py pattern) ─────────────────


def _authorized(update: Update) -> bool:
    """Return True if the message originates from the configured chat_id."""
    from config.settings import get_settings
    return update.effective_chat.id == get_settings().telegram_chat_id


# ── Command handlers ──────────────────────────────────────────────────────────


async def cmd_affiliate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show today's brief status.

    Queries the SQLite `briefs` table for today's date and returns:
      - brief_id
      - status (draft | ready | posted | archived)
      - offer name + chosen hook (if set)
      - script word count (if set)

    Usage: /affiliate
    """
    if not _authorized(update):
        return
    ...


async def cmd_affiliate_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger the daily pipeline for today (or a specified date).

    Runs build_daily_graph() asynchronously and streams progress updates
    to Telegram as each node completes.  If a brief for today already exists
    with status='ready', asks for confirmation before overwriting.

    Usage: /affiliate_run [YYYY-MM-DD]
    """
    if not _authorized(update):
        return
    ...


async def cmd_affiliate_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log performance metrics for a posted video.

    Accepts either:
      - JSON: /affiliate_log {"video_id": "...", "views": 12000, ...}
      - Natural language: /affiliate_log video abc123 got 12k views, 300 likes

    Invokes PerformanceLoggerAgent to parse and persist the metrics.

    Usage: /affiliate_log <json_or_text>
    """
    if not _authorized(update):
        return
    ...


async def cmd_affiliate_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a 7-day performance summary table.

    Queries the `performance` and `videos` tables and renders a Markdown table:
    | Date | Videos | Total Views | Conversions |
    |------|--------|-------------|-------------|

    Usage: /affiliate_stats [days=7]
    """
    if not _authorized(update):
        return
    ...


async def cmd_affiliate_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger the weekly review pipeline or show the latest saved report.

    If called with no args, returns the most recent report_markdown stored in
    the weekly review checkpoint.
    If called with --run, triggers build_weekly_graph() for the current week.

    Usage: /affiliate_weekly [--run]
    """
    if not _authorized(update):
        return
    ...


async def cmd_affiliate_winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current winners_pattern entries from SQLite.

    Displays up to 10 most recent patterns sorted by confidence_score desc.
    Each entry shows: pattern_type, confidence_score, description (truncated).

    Usage: /affiliate_winner [pattern_type]
           e.g. /affiliate_winner hook
    """
    if not _authorized(update):
        return
    ...


# ── Registration ──────────────────────────────────────────────────────────────


def register_affiliate_commands(app: Application) -> None:
    """Register all affiliate_factory command handlers with the PTB Application.

    Call this function once inside bot/telegrambot.build_application(),
    after the existing core command registrations.

    Args:
        app: The PTB Application instance returned by Application.builder().build().

    Example (bot/telegrambot.py):
        from affiliate_factory.telegram_commands import register_affiliate_commands

        def build_application() -> Application:
            app = Application.builder().token(...).post_init(_post_init).build()
            # ... existing handlers ...
            register_affiliate_commands(app)   # ← add this line
            return app
    """
    app.add_handler(CommandHandler("affiliate",         cmd_affiliate))
    app.add_handler(CommandHandler("affiliate_run",     cmd_affiliate_run))
    app.add_handler(CommandHandler("affiliate_log",     cmd_affiliate_log))
    app.add_handler(CommandHandler("affiliate_stats",   cmd_affiliate_stats))
    app.add_handler(CommandHandler("affiliate_weekly",  cmd_affiliate_weekly))
    app.add_handler(CommandHandler("affiliate_winner",  cmd_affiliate_winner))

    logger.info("affiliate_factory: 6 Telegram commands registered.")

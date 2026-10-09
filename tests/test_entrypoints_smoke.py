# tests/test_entrypoints_smoke.py
"""
Giriş noktaları smoke testleri — port açılmaz, polling başlamaz, canlı API yok.

  - Telegram: modül import + Application kurulumu (ağsız) + handle_message akışı
  - FastAPI : ASGI üzerinden bellek içi istekler (uvicorn yok)
  - Gerçek ChatAnthropic.with_structured_output(CEODecision) zinciri; yalnızca
    ağa giden _agenerate sahtelenir (tool şeması, tool_choice ve parser gerçek).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _repo_cwd(monkeypatch):
    """api.server StaticFiles('dashboard') ve FileResponse göreli yol kullanır."""
    monkeypatch.chdir(REPO_ROOT)


# ── Telegram ──────────────────────────────────────────────────────────────────

EXPECTED_COMMANDS = {
    "start", "help", "status", "agents", "history", "clear", "stats",
    "debug", "export", "research", "write", "market", "code",
}


def test_telegram_application_builds_offline_with_all_handlers():
    from bot import telegrambot

    app = telegrambot.build_application()          # ağ çağrısı yapmaz, polling başlatmaz

    handlers = app.handlers[0]
    commands = {c for h in handlers if hasattr(h, "commands") for c in h.commands}
    assert commands == EXPECTED_COMMANDS
    assert len(handlers) == len(EXPECTED_COMMANDS) + 1   # + metin MessageHandler


def _fake_update(chat_id: int, text: str):
    message = SimpleNamespace(text=text, reply_text=AsyncMock())
    return SimpleNamespace(effective_chat=SimpleNamespace(id=chat_id), message=message)


def _fake_context():
    return SimpleNamespace(bot=SimpleNamespace(send_chat_action=AsyncMock()))


@pytest.fixture
def telegram(monkeypatch):
    """Sıfır rate-limit durumu + sahte process_message."""
    from bot import telegrambot
    from core.rate_limiter import RateLimiter

    monkeypatch.setattr("core.rate_limiter._rate_limiter", RateLimiter())
    calls: list[tuple[int, str]] = []

    async def fake_process(chat_id, user_input):
        calls.append((chat_id, user_input))
        return "sahte yanıt", "DIRECT"

    monkeypatch.setattr(telegrambot, "process_message", fake_process)
    return SimpleNamespace(module=telegrambot, calls=calls)


@pytest.mark.asyncio
async def test_telegram_authorized_message_reaches_orchestrator_and_gets_reply(telegram):
    chat_id = telegram.module.settings.telegram_chat_id
    update = _fake_update(chat_id, "merhaba")

    await telegram.module.handle_message(update, _fake_context())

    assert telegram.calls == [(chat_id, "merhaba")]
    sent = [c.args[0] for c in update.message.reply_text.await_args_list]
    assert any("sahte yanıt" in s for s in sent)


@pytest.mark.asyncio
async def test_telegram_unauthorized_chat_is_ignored(telegram):
    update = _fake_update(telegram.module.settings.telegram_chat_id + 999, "merhaba")

    await telegram.module.handle_message(update, _fake_context())

    assert telegram.calls == []
    update.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_telegram_rejects_oversized_input_before_orchestrator(telegram):
    chat_id = telegram.module.settings.telegram_chat_id
    update = _fake_update(chat_id, "a" * 5000)           # limit: 4000

    await telegram.module.handle_message(update, _fake_context())

    assert telegram.calls == []
    update.message.reply_text.assert_awaited_once()


# ── FastAPI (ASGI, bellek içi) ────────────────────────────────────────────────

@pytest.fixture
def api(monkeypatch):
    from api import server

    server.active_tasks.clear()
    server.connected_clients.clear()
    calls: list[str] = []

    async def fake_process(chat_id, user_input):
        calls.append(user_input)
        return "api yanıtı", "CodeAgent"

    monkeypatch.setattr("core.orchestrator.process_message", fake_process)

    def client():
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server.app), base_url="http://test",
        )

    yield SimpleNamespace(server=server, client=client, calls=calls)
    server.active_tasks.clear()


@pytest.mark.asyncio
async def test_api_read_endpoints(api):
    async with api.client() as c:
        agents = await c.get("/agents")
        tasks = await c.get("/tasks")
        root = await c.get("/")

    assert agents.status_code == 200
    assert set(agents.json()) == {"ResearchAgent", "WriterAgent", "MarketAnalysisAgent", "CodeAgent"}
    assert set(agents.json().values()) == {"idle"}
    assert tasks.json() == []
    assert root.status_code == 200 and "html" in root.headers["content-type"]


@pytest.mark.asyncio
async def test_api_task_runs_through_process_message(api):
    async with api.client() as c:
        resp = await c.post("/task", json={"message": "kod yaz"})
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

        for _ in range(100):                              # arka plan task'ı bitene kadar (≤ 2 sn)
            if api.server.active_tasks[task_id]["status"] != "running":
                break
            await asyncio.sleep(0.02)

        listed = (await c.get("/tasks")).json()

    assert api.calls == ["kod yaz"]
    assert listed[0]["status"] == "done"
    assert listed[0]["agent"] == "CodeAgent"
    assert listed[0]["result"] == "api yanıtı"


def test_api_websocket_sends_init_snapshot(api):
    from starlette.testclient import TestClient

    with TestClient(api.server.app) as client, client.websocket_connect("/ws") as ws:
        init = ws.receive_json()

    assert init["type"] == "init"
    assert set(init["agents"]) == {"ResearchAgent", "WriterAgent", "MarketAnalysisAgent", "CodeAgent"}


# ── Gerçek ChatAnthropic.with_structured_output(CEODecision) ──────────────────

def _tool_call_result(args: dict) -> ChatResult:
    msg = AIMessage(content="", tool_calls=[{"name": "CEODecision", "args": args, "id": "toolu_test"}])
    return ChatResult(generations=[ChatGeneration(message=msg)])


@pytest.fixture
def anthropic_wire(monkeypatch):
    """ChatAnthropic gerçek; yalnızca ağa çıkan _agenerate yakalanır."""
    from langchain_anthropic import ChatAnthropic

    seen: dict = {}
    reply: dict = {"args": {"next_agent": "CodeAgent", "task": "t", "reason": "r"}}

    async def fake_agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        seen["kwargs"] = kwargs
        seen["messages"] = messages
        return _tool_call_result(reply["args"])

    monkeypatch.setattr(ChatAnthropic, "_agenerate", fake_agenerate)
    return SimpleNamespace(seen=seen, reply=reply)


@pytest.mark.asyncio
async def test_real_structured_output_chain_returns_ceo_decision(anthropic_wire):
    from core.orchestrator import CEODecision, _get_llm

    decision = await _get_llm().with_structured_output(CEODecision).ainvoke("istek")

    assert isinstance(decision, CEODecision)
    assert (decision.next_agent, decision.task, decision.reason) == ("CodeAgent", "t", "r")

    kwargs = anthropic_wire.seen["kwargs"]
    tool = kwargs["tools"][0]
    assert tool["name"] == "CEODecision"
    enum = tool["input_schema"]["properties"]["next_agent"]["enum"]
    assert set(enum) == {"ResearchAgent", "WriterAgent", "MarketAnalysisAgent", "CodeAgent", "DIRECT"}
    assert kwargs["tool_choice"]["name"] == "CEODecision"     # model aracı çağırmaya zorlanır


@pytest.mark.asyncio
async def test_supervisor_with_real_chain_falls_back_to_direct_on_invalid_agent(anthropic_wire):
    from core.orchestrator import supervisor_node

    anthropic_wire.reply["args"] = {"next_agent": "UydurmaAgent", "task": "t", "reason": "r"}

    update = await supervisor_node({"user_input": "selam", "history_summary": "-"})

    assert update["next_agent"] == "DIRECT"
    assert update["task"] == "selam"
    assert update["error"]                                    # hata sessizce yutulmadı, state'e yazıldı


@pytest.mark.asyncio
async def test_supervisor_with_real_chain_routes_valid_decision(anthropic_wire):
    from core.orchestrator import supervisor_node

    update = await supervisor_node({"user_input": "kod yaz", "history_summary": "-"})

    assert update == {"next_agent": "CodeAgent", "task": "t", "reason": "r"}
    prompt_text = anthropic_wire.seen["messages"][0].content
    assert "kod yaz" in prompt_text and '"next_agent"' in prompt_text


# ── Telegram komutları: MEMORY_ENABLED=false ──────────────────────────────────

@pytest.fixture
def memory_off(monkeypatch):
    from memory import database

    def boom(*_a, **_k):
        raise AssertionError("bellek kapalıyken Chroma/embedding başlatıldı")

    monkeypatch.setattr(database.settings, "memory_enabled", False)
    monkeypatch.setattr(database, "_managers", {})
    monkeypatch.setattr(database, "Chroma", boom)
    monkeypatch.setattr(database, "SentenceTransformerEmbeddings", boom)


@pytest.mark.asyncio
@pytest.mark.parametrize("command", ["cmd_history", "cmd_clear", "cmd_export", "cmd_status", "cmd_debug"])
async def test_memory_commands_say_memory_is_off_instead_of_faking_empty_results(
    telegram, memory_off, command,
):
    update = _fake_update(telegram.module.settings.telegram_chat_id, "/x")
    context = _fake_context()
    context.args = []

    await getattr(telegram.module, command)(update, context)

    texts = " ".join(c.args[0] for c in update.message.reply_text.await_args_list)
    assert "devre dışı" in texts
    for misleading in ("silindi", "Henüz kayıtlı", "bulunamadı", "0 kayıt"):
        assert misleading not in texts

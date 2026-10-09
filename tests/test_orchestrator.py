# tests/test_orchestrator.py
"""
Orkestratör regresyon testleri — canlı API yok, gerçek Chroma/embedding yok.

Kapsam:
  1. CEO prompt'u str.format ile hatasız render edilir          (P0-1)
  2. Mesaj graph'a girer, DIRECT ve uzman agent yollarına gider
  3. Async checkpoint gerçekten yazılır ve turlar arası birikir  (P0-2)
  4. Tekrarlı çağrılar / ayrı event loop'lar hata üretmez, thread sızdırmaz
"""

from __future__ import annotations

import asyncio
import threading
import time
from types import SimpleNamespace
from typing import get_args

import pytest
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from config.prompts import AVAILABLE_AGENTS, get_ceo_prompt


# ── Sahte bileşenler ──────────────────────────────────────────────────────────

class FakeStructured:
    """llm.with_structured_output(CEODecision) sonucu."""

    def __init__(self, decision):
        self.decision = decision
        self.prompts: list[str] = []

    def _answer(self, prompt):
        self.prompts.append(prompt)
        if isinstance(self.decision, Exception):
            raise self.decision
        return self.decision

    def invoke(self, prompt):
        return self._answer(prompt)

    async def ainvoke(self, prompt):
        return self._answer(prompt)


class FakeLLM:
    """ChatAnthropic yerine geçer: hem CEO hem agent çağrıları için."""

    def __init__(self, decision=None, reply="R"):
        self.structured = FakeStructured(decision)
        self.reply = reply
        self.prompts: list = []

    def with_structured_output(self, _schema):
        return self.structured

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(content=self.reply)

    async def ainvoke(self, prompt):
        return self.invoke(prompt)


class FakeMemory:
    def __init__(self):
        self.saved: list[tuple[str, str, str]] = []

    def get_history_summary(self, limit=None):
        return "Önceki konuşma yok."

    def get_relevant_context(self, query, k=4):
        return ""

    def save_turn(self, user_msg, assistant_msg, agent="DIRECT"):
        self.saved.append((user_msg, assistant_msg, agent))


def _decision(next_agent="DIRECT", task="görev", reason="test"):
    from core.orchestrator import CEODecision
    return CEODecision(next_agent=next_agent, task=task, reason=reason)


@pytest.fixture
def jaq(monkeypatch, tmp_path):
    """Her test: kendi geçici checkpoint DB'si + sahte hafıza."""
    from core import orchestrator

    db_path = str(tmp_path / "checkpoints.db")
    monkeypatch.setattr(orchestrator.settings, "checkpoint_db_path", db_path)

    memory = FakeMemory()
    monkeypatch.setattr(orchestrator, "get_memory_manager", lambda chat_id: memory)
    monkeypatch.setattr("agents.base_agent.get_memory_manager", lambda chat_id: memory)

    def use_llm(llm):
        monkeypatch.setattr(orchestrator, "_get_llm", lambda: llm)
        # Uzman agent'lar kendi LLM'lerini BaseAgent.llm property'sinden alır
        from agents.base_agent import BaseAgent
        monkeypatch.setattr(BaseAgent, "llm", property(lambda self: llm))

    return SimpleNamespace(
        orchestrator=orchestrator, memory=memory, db_path=db_path, use_llm=use_llm,
    )


async def _read_thread_messages(db_path: str, thread_id: str) -> list[str]:
    async with AsyncSqliteSaver.from_conn_string(db_path) as saver:
        tup = await saver.aget_tuple({"configurable": {"thread_id": thread_id}})
    assert tup is not None, f"thread {thread_id} için checkpoint yok"
    return [m.content for m in tup.checkpoint["channel_values"]["messages"]]


# ── 1. CEO prompt (P0-1) ──────────────────────────────────────────────────────

def test_ceo_prompt_renders_with_runtime_values():
    rendered = get_ceo_prompt(AVAILABLE_AGENTS).format(
        user_input="Merhaba", history_summary="Önceki konuşma yok.",
    )
    for agent in AVAILABLE_AGENTS:
        assert agent in rendered
    assert "Merhaba" in rendered
    assert '"next_agent"' in rendered          # JSON şablonu bozulmadan geldi
    assert "{{" not in rendered and "}}" not in rendered


def test_ceo_prompt_keeps_braces_typed_by_user():
    user_input = 'şu json\'u incele {"a": 1} ve {x}'
    rendered = get_ceo_prompt(AVAILABLE_AGENTS).format(
        user_input=user_input, history_summary="-",
    )
    assert user_input in rendered


def test_literal_agent_names_match_available_agents():
    from core.orchestrator import AgentName
    assert set(get_args(AgentName)) - {"DIRECT"} == set(AVAILABLE_AGENTS)


def test_unknown_agent_routes_to_direct(jaq):
    route = jaq.orchestrator.route_after_supervisor
    assert route({"next_agent": "OlmayanAgent"}) == "direct"
    assert route({"next_agent": "CodeAgent"}) == "code"


# ── 2. Graph yolları ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_message_takes_direct_path(jaq):
    llm = FakeLLM(decision=_decision("DIRECT"), reply="Merhaba!")
    jaq.use_llm(llm)

    response, agent = await jaq.orchestrator.process_message(42, "Merhaba JAQ")

    assert (response, agent) == ("Merhaba!", "DIRECT")
    assert "Merhaba JAQ" in llm.structured.prompts[0]   # CEO prompt'u render edilip LLM'e gitti
    assert jaq.memory.saved == [("Merhaba JAQ", "Merhaba!", "DIRECT")]


@pytest.mark.asyncio
async def test_message_routes_to_specialist_agent(jaq):
    llm = FakeLLM(decision=_decision("CodeAgent", task="python fonksiyonu yaz"), reply="def f(): ...")
    jaq.use_llm(llm)

    response, agent = await jaq.orchestrator.process_message(42, "bir python fonksiyonu yaz")

    assert (response, agent) == ("def f(): ...", "CodeAgent")
    assert "python fonksiyonu yaz" in llm.prompts[0][0].content   # agent CEO'nun task'ını aldı
    assert jaq.memory.saved[-1][2] == "CodeAgent"


@pytest.mark.asyncio
async def test_ceo_failure_falls_back_to_direct(jaq):
    jaq.use_llm(FakeLLM(decision=RuntimeError("LLM down"), reply="yedek yanıt"))

    response, agent = await jaq.orchestrator.process_message(42, "merhaba")

    assert (response, agent) == ("yedek yanıt", "DIRECT")


# ── 3. Async checkpoint (P0-2) ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_checkpoint_is_written_and_accumulates_across_turns(jaq):
    jaq.use_llm(FakeLLM(decision=_decision("DIRECT"), reply="R"))

    await jaq.orchestrator.process_message(42, "birinci")
    assert await _read_thread_messages(jaq.db_path, "42") == ["birinci", "R"]

    await jaq.orchestrator.process_message(42, "ikinci")
    assert await _read_thread_messages(jaq.db_path, "42") == ["birinci", "R", "ikinci", "R"]


@pytest.mark.asyncio
async def test_threads_are_isolated_per_chat(jaq):
    jaq.use_llm(FakeLLM(decision=_decision("DIRECT"), reply="R"))

    await jaq.orchestrator.process_message(1, "a")
    await jaq.orchestrator.process_message(2, "b")

    assert await _read_thread_messages(jaq.db_path, "1") == ["a", "R"]
    assert await _read_thread_messages(jaq.db_path, "2") == ["b", "R"]


# ── 4. Tekrar, eşzamanlılık, event loop ve kaynak temizliği ───────────────────

@pytest.mark.asyncio
async def test_repeated_and_concurrent_calls_in_one_loop(jaq):
    jaq.use_llm(FakeLLM(decision=_decision("DIRECT"), reply="R"))

    for i in range(3):
        assert await jaq.orchestrator.process_message(10, f"m{i}") == ("R", "DIRECT")

    results = await asyncio.gather(*(
        jaq.orchestrator.process_message(100 + n, f"eşzamanlı {n}") for n in range(4)
    ))
    assert results == [("R", "DIRECT")] * 4
    assert len(await _read_thread_messages(jaq.db_path, "10")) == 6


def test_separate_event_loops_share_one_database_without_leaking_threads(jaq):
    """
    Her asyncio.run() yeni bir loop'tur; eski loop'a bağlı kalıntı olmamalı.

    Not: thread sayısı tek başına "bağlantı kapandı" kanıtı DEĞİLDİR (aiosqlite thread'i
    nesne finalize olunca da durur); deterministik kapanış ayrı test edilir.
    """
    jaq.use_llm(FakeLLM(decision=_decision("DIRECT"), reply="R"))
    threads_before = threading.active_count()

    for i in range(3):
        result = asyncio.run(jaq.orchestrator.process_message(7, f"loop {i}"))
        assert result == ("R", "DIRECT")

    messages = asyncio.run(_read_thread_messages(jaq.db_path, "7"))
    assert messages == ["loop 0", "R", "loop 1", "R", "loop 2", "R"]

    deadline = time.monotonic() + 3          # aiosqlite worker thread'i kapanışta biraz gecikebilir
    while threading.active_count() > threads_before and time.monotonic() < deadline:
        time.sleep(0.05)
    assert threading.active_count() <= threads_before, "SQLite bağlantı thread'i sızdı"


@pytest.mark.asyncio
async def test_timeout_cancellation_closes_connection_and_db_stays_usable(jaq):
    """Telegram'daki asyncio.wait_for timeout'u uçuştaki graph'ı iptal eder."""
    class SlowLLM(FakeLLM):
        async def ainvoke(self, prompt):
            await asyncio.sleep(30)

    def own_threads() -> int:
        # asyncio_N = çalışan event loop'un kendi default executor'ı; loop kapanınca ölür.
        return sum(not t.name.startswith("asyncio_") for t in threading.enumerate())

    jaq.use_llm(SlowLLM(decision=_decision("DIRECT")))
    threads_before = own_threads()

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(jaq.orchestrator.process_message(5, "ilk"), timeout=0.5)

    deadline = time.monotonic() + 3
    while own_threads() > threads_before and time.monotonic() < deadline:
        await asyncio.sleep(0.05)
    assert own_threads() <= threads_before, "iptal sonrası SQLite thread'i sızdı"
    assert jaq.memory.saved == []                      # iptal edilen tur hafızaya yazılmadı

    jaq.use_llm(FakeLLM(decision=_decision("DIRECT"), reply="R"))
    assert await jaq.orchestrator.process_message(5, "yeni") == ("R", "DIRECT")
    assert (await _read_thread_messages(jaq.db_path, "5"))[-2:] == ["yeni", "R"]


@pytest.mark.asyncio
async def test_checkpointer_connection_is_closed_on_exit_and_on_error(jaq):
    """Kapanışı thread sayısıyla değil, bağlantının kendisiyle doğrula."""
    from memory.database import open_async_checkpointer

    async with open_async_checkpointer() as saver:
        conn = saver.conn
        await conn.execute("SELECT 1")                 # içeride açık
    with pytest.raises(ValueError):                    # aiosqlite: kapalı bağlantı
        await conn.execute("SELECT 1")

    with pytest.raises(RuntimeError, match="boom"):
        async with open_async_checkpointer() as saver:
            conn = saver.conn
            raise RuntimeError("boom")
    with pytest.raises(ValueError):                    # hata yolunda da kapanır
        await conn.execute("SELECT 1")

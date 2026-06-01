# core/orchestrator.py
"""
JAQ-AI v2.0 — Hierarchical LangGraph Orchestrator

Akış:
  START → supervisor → [ResearchAgent | WriterAgent | MarketAnalysisAgent |
                         CodeAgent | direct] → END

Özellikler:
  - Pydantic structured output (JSON parse hatası yok)
  - SQLite checkpointing (her tur persist edilir)
  - MemoryManager entegrasyonu (geçmiş otomatik inject)
  - Gerçek agent'lar (Phase 4 tamamlandı)
  - Timeout + hata yönetimi
"""

import logging
from typing import Literal, Annotated

from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from config.settings import get_settings
from config.prompts import get_ceo_prompt, DIRECT_RESPONSE_PROMPT, AVAILABLE_AGENTS
from memory.database import get_checkpointer, get_memory_manager
from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.code_agent import CodeAgent

logger = logging.getLogger(__name__)
settings = get_settings()


# ── 1. Graph State ─────────────────────────────────────────────────────────────

class JAQState(TypedDict):
    """
    LangGraph'ın her node arasında taşıdığı tam durum.
    `messages` otomatik append edilir (Annotated + add_messages).
    Diğer alanlar node tarafından üzerine yazılır.
    """
    messages: Annotated[list[BaseMessage], add_messages]
    chat_id: int
    user_input: str
    history_summary: str
    next_agent: str          # CEO kararı
    task: str                # Agent'a verilecek görev
    reason: str              # CEO'nun gerekçesi
    agent_output: str        # Seçilen agent'ın çıktısı
    final_response: str      # Telegram'a gönderilecek son metin
    error: str | None


# ── 2. CEO Structured Output Şeması ───────────────────────────────────────────

AgentName = Literal["ResearchAgent", "WriterAgent", "MarketAnalysisAgent", "CodeAgent", "DIRECT"]


class CEODecision(BaseModel):
    """CEO'nun routing kararı — LLM bunu doğrudan Pydantic objesi olarak döner."""
    next_agent: AgentName = Field(description="Görevi devralacak departman veya DIRECT")
    task: str = Field(description="Agent'a verilecek bağımsız, net görev açıklaması")
    reason: str = Field(description="Tek cümle neden bu seçim")


# ── 3. LLM ────────────────────────────────────────────────────────────────────

def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.model_name,
        api_key=settings.anthropic_api_key.get_secret_value(),
        temperature=settings.model_temperature,
        max_tokens=settings.model_max_tokens,
    )


# ── 4. Supervisor Node (CEO) ───────────────────────────────────────────────────

def supervisor_node(state: JAQState) -> dict:
    """
    CEO kararı: kullanıcı mesajını + geçmiş özeti okur,
    structured output ile hangi agent'ın çalışacağına karar verir.
    """
    llm = _get_llm()
    ceo_prompt = get_ceo_prompt(available_agents=AVAILABLE_AGENTS)

    formatted_prompt = ceo_prompt.format(
        user_input=state["user_input"],
        history_summary=state.get("history_summary", "Önceki konuşma yok."),
    )

    try:
        structured_llm = llm.with_structured_output(CEODecision)
        decision: CEODecision = structured_llm.invoke(formatted_prompt)
        logger.info(f"CEO kararı → agent={decision.next_agent}, reason={decision.reason}")
        return {
            "next_agent": decision.next_agent,
            "task": decision.task,
            "reason": decision.reason,
        }
    except Exception as e:
        logger.error(f"CEO karar hatası: {e}")
        return {
            "next_agent": "DIRECT",
            "task": state["user_input"],
            "reason": "CEO karar veremedi, direkt yanıt.",
            "error": str(e),
        }


# ── 5. Direct Response Node ───────────────────────────────────────────────────

def direct_node(state: JAQState) -> dict:
    """Agent gerektirmeyen yanıtlar (selamlama, basit soru vb.)."""
    llm = _get_llm()
    prompt = DIRECT_RESPONSE_PROMPT.format(user_input=state["user_input"])
    try:
        response = llm.invoke(prompt)
        text = response.content
    except Exception as e:
        logger.error(f"Direct node hatası: {e}")
        text = "Bir hata oluştu, lütfen tekrar deneyin."

    return {
        "agent_output": text,
        "final_response": text,
        "messages": [AIMessage(content=text)],
    }


# ── 6. Gerçek Agent Node'ları ──────────────────────────────────────────────────

def _run_agent(agent_cls, state: JAQState) -> dict:
    """
    Verilen agent sınıfını instantiate edip asenkron run() metodunu çalıştırır.
    LangGraph node'ları sync olduğundan asyncio.run() kullanır.
    """
    import asyncio
    task = state.get("task") or state["user_input"]
    chat_id = state["chat_id"]

    try:
        agent = agent_cls()
        result = asyncio.run(agent.run(task=task, chat_id=chat_id))
        output = result.output if result.success else f"Hata: {result.error}"
    except Exception as e:
        logger.error(f"{agent_cls.__name__} node hatası: {e}", exc_info=True)
        output = f"{agent_cls.__name__} çalışırken hata oluştu: {e}"

    return {
        "agent_output": output,
        "final_response": output,
        "messages": [AIMessage(content=output)],
    }


def research_node(state: JAQState) -> dict:
    return _run_agent(ResearchAgent, state)

def writer_node(state: JAQState) -> dict:
    return _run_agent(WriterAgent, state)

def market_node(state: JAQState) -> dict:
    return _run_agent(MarketAnalysisAgent, state)

def code_node(state: JAQState) -> dict:
    return _run_agent(CodeAgent, state)


# ── 7. Routing Fonksiyonu ─────────────────────────────────────────────────────

def route_after_supervisor(state: JAQState) -> str:
    """
    CEO'nun next_agent kararını LangGraph edge'ine çevirir.
    Bilinmeyen agent → DIRECT'e düşer.
    """
    mapping = {
        "ResearchAgent":       "research",
        "WriterAgent":         "writer",
        "MarketAnalysisAgent": "market",
        "CodeAgent":           "code",
        "DIRECT":              "direct",
    }
    route = mapping.get(state.get("next_agent", "DIRECT"), "direct")
    logger.debug(f"Routing → {route}")
    return route


# ── 8. Graph İnşası ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(JAQState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research",   research_node)
    graph.add_node("writer",     writer_node)
    graph.add_node("market",     market_node)
    graph.add_node("code",       code_node)
    graph.add_node("direct",     direct_node)

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "research": "research",
            "writer":   "writer",
            "market":   "market",
            "code":     "code",
            "direct":   "direct",
        },
    )

    for node in ("research", "writer", "market", "code", "direct"):
        graph.add_edge(node, END)

    return graph


# ── 9. Compiled Graph (Checkpointer ile) ─────────────────────────────────────

_compiled_graph = None


def get_compiled_graph():
    """Graph'ı bir kez derler, checkpointer bağlar, cache'de tutar."""
    global _compiled_graph
    if _compiled_graph is None:
        checkpointer = get_checkpointer()
        _compiled_graph = build_graph().compile(checkpointer=checkpointer)
        logger.info("LangGraph compiled, checkpointer bağlandı.")
    return _compiled_graph


# ── 10. Ana Entry Point ───────────────────────────────────────────────────────

async def process_message(chat_id: int, user_input: str) -> tuple[str, str]:
    """
    Telegram bot handler'ının çağırdığı tek fonksiyon.

    Her chat_id → ayrı LangGraph thread_id (konuşmalar izole).
    Geçmiş hafıza otomatik inject edilir.

    Returns:
        (final_response, agent_name) — yanıt metni + kullanılan agent adı
    """
    memory = get_memory_manager(chat_id)
    history_summary = memory.get_history_summary()

    initial_state: JAQState = {
        "messages":        [HumanMessage(content=user_input)],
        "chat_id":         chat_id,
        "user_input":      user_input,
        "history_summary": history_summary,
        "next_agent":      "",
        "task":            "",
        "reason":          "",
        "agent_output":    "",
        "final_response":  "",
        "error":           None,
    }

    config = {"configurable": {"thread_id": str(chat_id)}}
    result = {}

    try:
        graph = get_compiled_graph()
        result = await graph.ainvoke(initial_state, config=config)
        final = result.get("final_response", "Bir yanıt üretilemedi.")
    except Exception as e:
        logger.error(f"Graph invoke hatası: {e}", exc_info=True)
        final = "Bir hata oluştu. Lütfen tekrar deneyin."

    agent_used = result.get("next_agent", "DIRECT") or "DIRECT"

    try:
        memory.save_turn(user_msg=user_input, assistant_msg=final, agent=agent_used)
    except Exception as e:
        logger.warning(f"Hafıza kayıt hatası: {e}")

    return final, agent_used

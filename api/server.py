"""
JAQ-AI Dashboard API — FastAPI backend
Endpoints:
  GET  /            → dashboard/index.html
  GET  /agents      → agent durum listesi
  GET  /tasks       → görev geçmişi
  POST /task        → yeni görev gönder
  WS   /ws          → canlı event stream
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="JAQ-AI Dashboard", version="2.0")
app.mount("/static", StaticFiles(directory="dashboard"), name="static")

# ── State (in-memory) ────────────────────────────────────────────────────────

KNOWN_AGENTS = ["ResearchAgent", "WriterAgent", "MarketAnalysisAgent", "CodeAgent"]

agent_status: dict[str, str] = {a: "idle" for a in KNOWN_AGENTS}
active_tasks: dict[str, dict[str, Any]] = {}
connected_clients: list[WebSocket] = []


# ── WebSocket broadcast ───────────────────────────────────────────────────────

async def broadcast(event: dict) -> None:
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


# ── Request / Response Schemas ────────────────────────────────────────────────

class TaskRequest(BaseModel):
    message: str


class TaskQueued(BaseModel):
    task_id: str
    status: str = "queued"


# ── Background task runner ────────────────────────────────────────────────────

async def run_task(task_id: str, message: str) -> None:
    from core.orchestrator import process_message

    await broadcast({
        "type": "task_start",
        "task_id": task_id,
        "message": message,
        "ts": datetime.now().isoformat(),
    })

    try:
        # process_message async'tir, direkt await edilir
        final_response, agent_used = await process_message(chat_id=0, user_input=message)

        # Bilinen bir agent ise durumunu idle'a al
        if agent_used in agent_status:
            agent_status[agent_used] = "idle"
        else:
            # CEO "DIRECT" gibi bir değer döndürmüş olabilir
            agent_used = agent_used or "DIRECT"

        active_tasks[task_id].update({
            "status": "done",
            "agent": agent_used,
            "result": final_response,
            "finished_at": datetime.now().isoformat(),
        })

        await broadcast({
            "type": "task_done",
            "task_id": task_id,
            "agent": agent_used,
            "result": final_response,
            "ts": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Task {task_id} hatası: {e}", exc_info=True)
        active_tasks[task_id].update({
            "status": "error",
            "result": str(e),
            "finished_at": datetime.now().isoformat(),
        })
        await broadcast({
            "type": "task_error",
            "task_id": task_id,
            "error": str(e),
            "ts": datetime.now().isoformat(),
        })

    finally:
        # Tüm agent'ları idle'a döndür (basit güvence)
        for a in agent_status:
            agent_status[a] = "idle"
        await broadcast({"type": "agents_update", "agents": agent_status})


# ── HTTP Endpoints ────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("dashboard/index.html")


@app.get("/agents")
async def get_agents() -> dict:
    return agent_status


@app.get("/tasks")
async def get_tasks() -> list:
    return list(active_tasks.values())


@app.post("/task", response_model=TaskQueued)
async def create_task(req: TaskRequest) -> TaskQueued:
    task_id = uuid.uuid4().hex[:8]

    active_tasks[task_id] = {
        "id": task_id,
        "message": req.message,
        "status": "running",
        "agent": None,
        "result": None,
        "created_at": datetime.now().isoformat(),
        "finished_at": None,
    }

    # Hangi agent'ın çalışacağını bilmiyoruz henüz — hepsini "checking" göster
    await broadcast({
        "type": "agents_update",
        "agents": {a: "busy" if a == "ResearchAgent" else s for a, s in agent_status.items()},
    })

    asyncio.create_task(run_task(task_id, req.message))
    return TaskQueued(task_id=task_id)


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    connected_clients.append(ws)
    logger.info(f"WS bağlandı — toplam: {len(connected_clients)}")

    try:
        # Bağlantı açılır açılmaz güncel durumu gönder
        await ws.send_json({
            "type": "init",
            "agents": agent_status,
            "tasks": list(active_tasks.values()),
        })

        while True:
            # keep-alive ping — client'tan herhangi bir mesaj bekle
            await asyncio.wait_for(ws.receive_text(), timeout=30)

    except asyncio.TimeoutError:
        # 30s'de ping gelmedi, bağlantı hâlâ açık — devam et
        pass
    except WebSocketDisconnect:
        pass
    finally:
        if ws in connected_clients:
            connected_clients.remove(ws)
        logger.info(f"WS bağlantısı kapandı — kalan: {len(connected_clients)}")

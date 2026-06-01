"""API 服务器 — 说谎者游戏

提供 REST API 用于远程控制游戏。
启动: uvicorn server:app --reload
"""

from __future__ import annotations
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="说谎者 AI Agent 游戏", version="1.0.0")

# 游戏实例（单例）
_engine = None


class GameStartRequest(BaseModel):
    players: int = 9
    liars: int = 1
    rounds: int = 3
    host: str = "人羊"
    reveal_thinking: bool = False


class GameStatusResponse(BaseModel):
    running: bool
    cycle: int
    phase: str
    participants: list[str]


@app.get("/")
def root():
    return {"game": "说谎者", "version": "1.0.0", "world": "终焉之地"}


@app.post("/game/start")
def start_game(req: GameStartRequest):
    global _engine
    from config import GameConfig, LLMConfig
    from game_engine import GameEngine
    from llm_client import LLMClient

    config = GameConfig()
    config.total_players = req.players
    config.liar_count = req.liars
    config.rounds = req.rounds
    config.host_name = req.host
    config.reveal_thinking = req.reveal_thinking

    llm = LLMClient()
    _engine = GameEngine(config=config, llm=llm)

    game, session = _engine.create_game()
    return {
        "status": "created",
        "session_id": session.id,
        "participants": [p.name for p in session.participants],
    }


@app.get("/game/status")
def game_status():
    if _engine is None:
        return {
            "running": False,
            "cycle": 0,
            "phase": "none",
            "participants": [],
        }
    return {
        "running": True,
        "cycle": _engine.current_cycle,
        "phase": "idle",
        "participants": [],
    }


@app.post("/game/run")
def run_game():
    if _engine is None:
        raise HTTPException(400, "请先创建游戏 POST /game/start")
    result = _engine.run_single_game()
    return result.model_dump()


@app.get("/game/memories/{character_name}")
def get_memories(character_name: str):
    if _engine is None:
        raise HTTPException(400, "请先创建游戏")
    return _engine.mem_mgr.load(character_name)

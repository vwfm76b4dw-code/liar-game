"""数据模型 -- 说谎者 AI Agent 游戏
基于《十日终焉》世界观
"""
from __future__ import annotations
import uuid, json
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field

def _uid(): return uuid.uuid4().hex[:8]
def _now(): return datetime.now(timezone.utc).strftime('%H:%M:%S')

# ---- 身份 ----
class Role(StrEnum):
    HONEST = '诚实者'
    LIAR = '说谎者'
    HOST = '生肖'

class ZodiacTier(StrEnum):
    HEAVEN = '天级'
    EARTH = '地级'
    HUMAN = '人级'

# ---- 回响 ----
class EchoDef(BaseModel):
    name: str
    description: str
    awakening_condition: str
    ability_effect: str

# ---- 角色人设 ----
class Personality(BaseModel):
    name: str
    age: int
    background: str
    traits: list[str] = []
    style: str = ''
    strategy: str = ''
    organization: str = ''
    echo: Optional[EchoDef] = None

# ---- 玩家 ----
class Player(BaseModel):
    id: str = Field(default_factory=_uid)
    name: str
    personality: Personality
    role: Role
    is_alive: bool = True
    awakened: bool = False
    dao: int = 0
    cycle_memories: list[dict] = []

# ---- 生肖主持人 ----
class ZodiacHost(BaseModel):
    id: str = Field(default_factory=_uid)
    name: str
    mask_animal: str
    tier: ZodiacTier
    personality: Personality
    cruelty: int = 5
    style: str = ''

# ---- 对话事件 ----
class DialogEvent(BaseModel):
    id: str = Field(default_factory=_uid)
    round_num: int
    speaker: str
    msg_type: str = 'speak'
    content: str
    target: str = ''
    internal_state: dict = Field(default_factory=lambda: {
        'emotion': '', 'thought': '', 'hp': 100
    })
    timestamp: str = Field(default_factory=_now)

# ---- 问答记录 ----
class QARecord(BaseModel):
    round_num: int
    asker: str
    respondent: str
    question: str
    answer: str

# ---- 投票 ----
class Vote(BaseModel):
    voter: str
    target: str
    reason: str
    timestamp: str = Field(default_factory=_now)

# ---- 游戏阶段 ----
class GamePhase(StrEnum):
    SETUP = 'setup'
    INTRO = 'intro'
    QUESTION = 'question'
    ANSWER = 'answer'
    DISCUSSION = 'discussion'
    VOTING = 'voting'
    RESULT = 'result'
    CYCLE_END = 'cycle_end'

# ---- 游戏类型 ----
class GameType(StrEnum):
    LIAR = '说谎者'
    YES_NO = '是与非'
    MUSHROOM = '雨后春笋'

# ---- 游戏会话 ----
class GameSession(BaseModel):
    id: str = Field(default_factory=_uid)
    game_type: GameType = GameType.LIAR
    phase: GamePhase = GamePhase.SETUP
    cycle_number: int = 1
    host: Optional[ZodiacHost] = None
    participants: list[Player] = []
    rounds: list[dict] = []
    votes: list[Vote] = []
    winner: Optional[Role] = None
    logs: list[DialogEvent] = []

# ---- 轮回记忆 ----
class CycleMemory(BaseModel):
    cycle_id: int
    event_type: str
    description: str
    emotion: str = ''
    importance: int = 3
    timestamp: str = Field(default_factory=_now)

# ---- 回响觉醒结果 ----
class AwakeningResult(BaseModel):
    character_name: str
    awakened: bool
    echo_name: str = ''
    trigger_event: str = ''
    memories_retained: list[CycleMemory] = []

# ---- 游戏结果 ----
class GameResult(BaseModel):
    winner: Role
    liars: list[str] = []
    liars_caught: list[str] = []
    liars_escaped: list[str] = []
    vote_tally: dict[str, int] = {}
    votes_detail: list[dict] = []
    awakening_results: list[AwakeningResult] = []
    summary: str = ''

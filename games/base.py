"""游戏基类 — 所有游戏类型的抽象基类"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from models import GameSession, GamePhase, GameResult, GameType


class BaseGame(ABC):
    """游戏基类"""

    game_type: GameType

    def __init__(self, session: GameSession):
        self.session = session
        self.phase = GamePhase.SETUP

    @abstractmethod
    def setup(self):
        """初始化游戏：分配角色等"""
        ...

    @abstractmethod
    def run_round(self, round_num: int):
        """运行一轮游戏"""
        ...

    @abstractmethod
    def run_voting(self):
        """运行投票阶段"""
        ...

    @abstractmethod
    def determine_result(self) -> GameResult:
        """判定胜负"""
        ...

    @abstractmethod
    def run(self) -> GameResult:
        """运行完整游戏"""
        ...

    def next_phase(self, phase: GamePhase):
        self.phase = phase
        self.session.phase = phase

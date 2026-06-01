"""游戏引擎 — 轮回调度器 + 游戏编排

管理：
- 游戏创建与初始化
- 角色分配（随机抽取+随机身份）
- 多轮回调度
- 终焉之日处理
"""

from __future__ import annotations
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import GameConfig, load_characters, pick_zodiac
from llm_client import LLMClient
from models import (
    GameSession, GamePhase, GameResult, GameType, Role,
    Player, ZodiacHost, Personality, EchoDef,
)
from agent import ParticipantAgent, ZodiacAgent
from memory_manager import MemoryManager
from echo_system import EchoSystem
from games.liar_game import LiarGame


class GameEngine:
    """游戏引擎：管理完整的游戏生命周期"""

    def __init__(
        self,
        config: Optional[GameConfig] = None,
        llm: Optional[LLMClient] = None,
    ):
        self.config = config or GameConfig()
        self.llm = llm or LLMClient()
        self.mem_mgr = MemoryManager()
        self.echo_sys = EchoSystem()
        self.current_cycle = 1

    # ── 创建游戏 ───────────────────────────────

    def create_game(self) -> tuple[LiarGame, GameSession]:
        """创建一局说谎者游戏"""

        # 加载角色数据
        all_characters = load_characters()
        total = self.config.total_players
        liar_count = self.config.liar_count

        # 随机抽取角色
        selected = random.sample(all_characters, min(total, len(all_characters)))
        random.shuffle(selected)

        # 随机分配身份
        roles = [Role.LIAR] * liar_count + [Role.HONEST] * (len(selected) - liar_count)
        random.shuffle(roles)

        # 创建玩家
        players = []
        for persona, role in zip(selected, roles):
            # 加载跨轮回记忆
            mem_data = self.mem_mgr.load(persona.name)
            awakened = mem_data.get("awakened", False)
            cycle_memories = [
                dict(m) if hasattr(m, 'model_dump') else m
                for m in self.mem_mgr.get_cycle_memories(persona.name, self.current_cycle)
            ]

            player = Player(
                name=persona.name,
                personality=persona,
                role=role,
                awakened=awakened,
                cycle_memories=cycle_memories,
            )
            players.append(player)

        # 创建参与者Agent
        participants = [
            ParticipantAgent(
                player=p, llm=self.llm, mem_mgr=self.mem_mgr,
                total_players=len(players), liar_count=liar_count,
                total_rounds=self.config.rounds,
                host_name=self.config.host_name,
            )
            for p in players
        ]

        # 创建生肖主持人
        zodiac_data = pick_zodiac(self.config.host_name)
        if zodiac_data is None:
            zodiac_data = self._default_host()
        host = ZodiacAgent(zodiac_data, self.llm)

        # 创建会话
        session = GameSession(
            game_type=GameType.LIAR,
            cycle_number=self.current_cycle,
            host=zodiac_data,
            participants=players,
        )

        # 创建游戏
        game = LiarGame(
            session=session,
            llm=self.llm,
            participants=participants,
            host=host,
            mem_mgr=self.mem_mgr,
            echo_sys=self.echo_sys,
            rounds=self.config.rounds,
            reveal_thinking=self.config.reveal_thinking,
        )

        return game, session

    # ── 运行单轮 ───────────────────────────────

    def run_single_game(self) -> GameResult:
        """运行一局游戏"""
        game, session = self.create_game()
        return game.run()

    # ── 运行多轮回 ─────────────────────────────

    def run_cycles(self, num_cycles: int = 3) -> list[GameResult]:
        """运行多个轮回"""
        results = []
        for i in range(num_cycles):
            self.current_cycle = i + 1
            print(f"\n{'='*50}")
            print(f"  第 {self.current_cycle} 轮回 — 终焉之地")
            print(f"{'='*50}")
            result = self.run_single_game()
            results.append(result)
        return results

    # ── 辅助 ───────────────────────────────────

    def _default_host(self) -> ZodiacHost:
        """默认主持人：人羊"""
        return ZodiacHost(
            name="人羊",
            mask_animal="羊",
            tier="人级",
            personality=Personality(
                name="人羊", age=0,
                background="终焉之地的游戏主持人，戴着羊面具。残忍而优雅，享受参与者的绝望。",
                traits=["残忍", "优雅", "病态"],
                style="礼貌而压迫感十足",
                strategy="严格执行规则",
            ),
            cruelty=7,
            style="礼貌而压迫感十足",
        )

    # ── 日志 ───────────────────────────────────

    def save_log(self, result: GameResult, filepath: str = "logs/game.json"):
        """保存游戏日志"""
        from pathlib import Path
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        log = {
            "cycle": self.current_cycle,
            "timestamp": datetime.now().isoformat(),
            "result": result.model_dump(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        return str(path)

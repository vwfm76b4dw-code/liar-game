"""说谎者游戏 — 核心游戏逻辑

基于《十日终焉》说谎者游戏：
- 9名参与者，1名说谎者
- N轮问答 + 投票
- 生肖主持人
"""

from __future__ import annotations
import random
from typing import Optional
from models import (
    GameSession, GamePhase, GameResult, GameType, Role,
    QARecord, Vote, DialogEvent, AwakeningResult,
)
from agent import ParticipantAgent, ZodiacAgent
from llm_client import LLMClient
from memory_manager import MemoryManager
from echo_system import EchoSystem
from games.base import BaseGame


class LiarGame(BaseGame):
    """说谎者游戏"""

    game_type = GameType.LIAR

    def __init__(
        self,
        session: GameSession,
        llm: LLMClient,
        participants: list[ParticipantAgent],
        host: ZodiacAgent,
        mem_mgr: Optional[MemoryManager] = None,
        echo_sys: Optional[EchoSystem] = None,
        rounds: int = 3,
        reveal_thinking: bool = False,
    ):
        super().__init__(session)
        self.llm = llm
        self.participants = participants
        self.host = host
        self.mem_mgr = mem_mgr or MemoryManager()
        self.echo_sys = echo_sys or EchoSystem()
        self.total_rounds = rounds
        self.reveal_thinking = reveal_thinking
        self.all_qa: list[QARecord] = []
        self.votes: list[Vote] = []
        self.dialog_log: list[DialogEvent] = []

    # ── 初始化 ─────────────────────────────────

    def setup(self):
        """角色已在外部分配好，此处更新Agent参数"""
        self.phase = GamePhase.SETUP
        total = len(self.participants)
        liars = sum(1 for a in self.participants if a.is_liar)
        for agent in self.participants:
            agent.update_params(total, liars, self.total_rounds, self.host.name)

    # ── 运行完整游戏 ───────────────────────────

    def run(self) -> GameResult:
        self.setup()

        # 生肖宣布游戏开始
        intro = self.host.announce_game([a.name for a in self.participants])
        self._log_event(self.host.name, "announce", intro)

        # 多轮问答
        for r in range(1, self.total_rounds + 1):
            self.run_round(r)

        # 投票
        self.run_voting()

        # 判定
        return self.determine_result()

    # ── 单轮问答 ──────────────────────────────

    def run_round(self, round_num: int):
        self.phase = GamePhase.QUESTION

        order = list(range(len(self.participants)))
        random.shuffle(order)

        for idx in order:
            asker = self.participants[idx]
            others = [a.name for a in self.participants if a.name != asker.name]

            # 提问
            target_name, question, thinking = asker.ask_question(round_num, others)
            if self.reveal_thinking:
                self._log_event(asker.name, "thought", thinking)

            question_event = DialogEvent(
                round_num=round_num, speaker=asker.name,
                msg_type="question", content=question, target=target_name,
                internal_state={"thought": thinking},
            )
            self.dialog_log.append(question_event)

            # 回答
            respondent = self._find_agent(target_name)
            if respondent is None:
                continue

            answer, resp_thinking = respondent.answer_question(round_num, asker.name, question)
            if self.reveal_thinking:
                self._log_event(respondent.name, "thought", resp_thinking)

            answer_event = DialogEvent(
                round_num=round_num, speaker=respondent.name,
                msg_type="answer", content=answer, target=asker.name,
                internal_state={"thought": resp_thinking},
            )
            self.dialog_log.append(answer_event)

            # 记录问答
            qa = QARecord(
                round_num=round_num,
                asker=asker.name,
                respondent=respondent.name,
                question=question,
                answer=answer,
            )
            self.all_qa.append(qa)

            # 所有Agent观察
            for agent in self.participants:
                agent.observe(qa)

            # 生肖评论
            comment = self.host.comment(
                round_num,
                f"{asker.name}问{respondent.name}：{question} → {respondent.name}答：{answer}",
            )
            self._log_event(self.host.name, "comment", comment)

        # 本轮结束
        self.session.rounds.append({
            "round": round_num,
            "qa_pairs": [
                {"asker": q.asker, "respondent": q.respondent,
                 "question": q.question, "answer": q.answer}
                for q in self.all_qa
                if q.round_num == round_num
            ],
        })

    # ── 投票 ───────────────────────────────────

    def run_voting(self):
        self.phase = GamePhase.VOTING
        all_names = [a.name for a in self.participants]

        for agent in self.participants:
            results = agent.vote(1, [n for n in all_names if n != agent.name])
            for target, reason in results:
                vote = Vote(voter=agent.name, target=target, reason=reason)
                self.votes.append(vote)
                self._log_event(agent.name, "vote", f"投票给 {target}：{reason}")

    # ── 判定胜负 ──────────────────────────────

    def determine_result(self) -> GameResult:
        self.phase = GamePhase.RESULT

        liars = [a for a in self.participants if a.is_liar]
        liar_names = {a.name for a in liars}

        # 统计票数
        vote_tally: dict[str, int] = {}
        for v in self.votes:
            vote_tally[v.target] = vote_tally.get(v.target, 0) + 1

        # 得票最高的N个被"找出"（N = 说谎者数量）
        ranked = sorted(vote_tally.items(), key=lambda x: x[1], reverse=True)
        top_n = {name for name, _ in ranked[:len(liar_names)]}

        liars_caught = liar_names & top_n
        liars_escaped = liar_names - top_n
        honest_win = len(liars_escaped) == 0

        # 回响觉醒判定
        awakening_results = self._check_awakening()

        result = GameResult(
            winner=Role.HONEST if honest_win else Role.LIAR,
            liars=list(liar_names),
            liars_caught=list(liars_caught),
            liars_escaped=list(liars_escaped),
            vote_tally=vote_tally,
            votes_detail=[v.model_dump() for v in self.votes],
            awakening_results=awakening_results,
            summary=f"{'诚实者' if honest_win else '说谎者'}获胜。"
                    f"找出：{liars_caught or '无'}，逃脱：{liars_escaped or '无'}。",
        )

        # 处理终焉之日：保存觉醒者记忆
        self._handle_cycle_end(awakening_results)

        return result

    # ── 回响觉醒 ───────────────────────────────

    def _check_awakening(self) -> list[AwakeningResult]:
        results = []
        events = [e.model_dump() for e in self.dialog_log]
        for agent in self.participants:
            echo_name = agent.player.personality.echo.name if agent.player.personality.echo else None
            result = self.echo_sys.check_awakening(
                agent.name, echo_name, events, self.session.cycle_number,
            )
            if result.awakened:
                agent.player.awakened = True
            results.append(result)
        return results

    # ── 终焉之日 ───────────────────────────────

    def _handle_cycle_end(self, results: list[AwakeningResult]):
        """轮回结束：保存觉醒者记忆，清理未觉醒者"""
        for r in results:
            if r.awakened and r.memories_retained:
                for mem in r.memories_retained:
                    self.mem_mgr.add_memory(r.character_name, mem)

        # 清理未觉醒者记忆
        all_names = [a.name for a in self.participants]
        awakened = {r.character_name for r in results if r.awakened}
        non_awakened = [n for n in all_names if n not in awakened]
        self.mem_mgr.wipe_non_awakened(non_awakened)

    # ── 辅助 ───────────────────────────────────

    def _find_agent(self, name: str) -> Optional[ParticipantAgent]:
        for a in self.participants:
            if a.name == name:
                return a
        return None

    def _log_event(self, speaker: str, msg_type: str, content: str):
        self.dialog_log.append(DialogEvent(
            round_num=getattr(self, '_current_round', 0),
            speaker=speaker, msg_type=msg_type, content=content,
        ))

"""说谎者 — 交互式网页版
人羊半自动：人类玩家扮演人羊主持游戏，AI参与者自动进行问答。
忠于《十日终焉》世界观。
"""

from __future__ import annotations
import asyncio, json, os, random, sys, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import GameConfig, LLMConfig, load_characters, pick_zodiac
from llm_client import LLMClient
from models import Role, Player, QARecord, Vote, AwakeningResult
from agent import ParticipantAgent, ZodiacAgent
from memory_manager import MemoryManager
from echo_system import EchoSystem

_executor = ThreadPoolExecutor(max_workers=2)

async def _run_blocking(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: fn(*args, **kwargs))

app = FastAPI(title="说谎者 — 终焉之地")

# 静态文件（字体、图片）
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ── GameState ──

class GameState:
    def __init__(self):
        self.llm = LLMClient()
        self.config = GameConfig()
        self.mem_mgr = MemoryManager()
        self.echo_sys = EchoSystem(llm=self.llm)
        self.participants: list[ParticipantAgent] = []
        self.host: Optional[ZodiacAgent] = None
        self.players: list[Player] = []
        self.current_cycle = 1
        self.phase = "idle"
        self.round_num = 0
        self.total_rounds = 3
        self.all_qa: list[QARecord] = []
        self.votes: list[Vote] = []
        self.dialog_log: list[dict] = []
        self.awakening_results: list[AwakeningResult] = []
        self.total_words = 0
        self.game_start_time: float = 0.0
        self.auto_mode = False
        self.auto_paused = False
        self.auto_stopped = False
        self._auto_task: Optional[asyncio.Task] = None
        # 手动操控
        self.manual_players: set[str] = set()
        self.awaiting_manual: Optional[dict] = None
        self.manual_event = asyncio.Event()
        self.manual_input_data = ""
        # 视角系统
        self.current_perspective: str = "host"
        self.character_auto: dict[str, bool] = {}
        self._discussion_active = False

    def reset_cycle(self):
        self.phase = "intro"
        self.round_num = 0
        self.all_qa = []
        self.votes = []
        self.awakening_results = []
        self.echo_sys.reset_cycle()
        if len(self.dialog_log) > 200:
            self.dialog_log = self.dialog_log[-100:]

    def log(self, speaker: str, content: str, msg_type: str = "speak"):
        if msg_type in ("ai", "host", "vote", "echo"):
            self.total_words += len(content)
        entry = {
            "id": uuid.uuid4().hex[:6],
            "speaker": speaker,
            "content": content,
            "type": msg_type,
            "round": self.round_num,
            "cycle": self.current_cycle,
            "timestamp": __import__("datetime").datetime.now().strftime("%H:%M:%S"),
        }
        self.dialog_log.append(entry)
        return entry

state = GameState()


# ── 自动流程 ──

async def _auto_loop():
    """自动推进游戏流程"""
    while not state.auto_stopped:
        if state.auto_paused:
            await asyncio.sleep(0.5)
            continue
        try:
            phase = state.phase
            if phase == "opening":
                await _exec_action("do_opening")
            elif phase == "intro":
                await _exec_action("use_intro")
            elif phase == "storytelling":
                await asyncio.sleep(1)
            elif phase == "discussion":
                # 自动恢复被中断的讨论
                if state.auto_mode and not state.auto_paused and not state._discussion_active:
                    await _run_freediscussion()
                else:
                    await asyncio.sleep(1)
            elif phase == "round_end":
                await _exec_action("start_round" if state.round_num < state.total_rounds else "run_voting")
            elif phase == "voting":
                await _exec_action("run_voting")
            elif phase == "result_pending":
                await _exec_action("announce_result")
            elif phase == "result":
                await asyncio.sleep(5)
                if not state.auto_stopped:
                    await _exec_action("next_cycle")
            elif phase == "idle":
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"[auto] error: {e}")
            await asyncio.sleep(2)

async def _exec_action(action: str) -> None:
    """执行动作并更新状态"""
    body = {"action": action}
    # 模拟请求对象
    from fastapi import Request
    # 直接调用内部逻辑
    if action == "do_opening":
        state.phase = "intro"
        state.log("系统", "座钟响了。分针与时针同时指向了「十二」。房间之外很遥远的地方，传来了低沉的钟声。", "scene")
        state.log("系统", "十个人慢慢苏醒了。他们迷惘地看了看四周，又疑惑地看了看对方。", "scene")
        state.log("🐑 人羊", "「早安，九位。」", "host")
        state.log("系统", "山羊头的声音从面具后传出，带着一股膻腥味。", "scene")
        state.log("系统", "乔家劲愣了几秒，带着犹豫开口：「你……是谁？」", "ai")
        state.log("🐑 人羊", "「相信你们都有这个疑问，那我就跟九位介绍一下。」", "host")
        state.log("🐑 人羊", "「我是「人羊」，而你们是「参与者」。如今把你们聚在一起，是为了参与一个游戏，最终创造一个「神」。」", "host")
        state.log("系统", "人羊缓缓来到一个年轻人身后。那年轻人脸上洋溢着诡异的微笑。", "scene")
        state.log("系统", "只听一声闷响——人羊把年轻人的头狠狠撞在了桌面上。", "scene")
        state.log("系统", "粉白色的东西如倾洒的颜料，在桌面上横向铺开。每个人的脸旁都溅到了血点。", "scene")
        state.log("系统", "年轻人的头颅在桌面上被撞了个粉碎。房间外，再次响起了一阵遥远的钟声。", "scene")
        state.log("系统", "坐在死者右边的女生面容扭曲，放声尖叫。", "ai")
        state.log("🐑 人羊", "「之所以准备了十个人，是为了用其中一人让你们安静下来。」", "host")
        state.log("系统", "人羊从裤子口袋中抽出一小叠卡片，那卡片看起来有扑克牌大小，背面写着「女娲游戏」四个字。", "scene")
        state.log("系统", "「下面，请大家抽卡。」人羊将卡片在桌面上摊开。", "host")
        state.log("系统", "九个人依次抽了一张卡。甜甜翻开卡面，手指微微颤抖。每个人的表情各异——有人皱眉、有人沉默、有人露出诡异的微笑。", "scene")
        state.log("系统", "人羊缓缓扫视众人：「你们当中，有且只有一个说谎者。抽到说谎者的人，必须在故事中掺杂谎言。」", "host")
        intro = await _run_blocking(state.host.announce_game, [a.name for a in state.participants])
        state.log(f"🐑 {state.config.host_name}", f"「{intro}」", "speak")
    elif action == "use_intro":
        state.phase = "storytelling"
        state.round_num = 0
        state.log("系统", "═════ 讲故事阶段 ═════", "system")
        state.log("系统", "人羊宣布规则：「有且只有一个说谎者」。每人轮流讲述死亡故事。", "system")
        state.log("系统", "按顺序：甜甜→乔家劲→肖冉→赵海博→韩一墨→章晨泽→李尚武→林檎→齐夏。", "system")
        clockwise_order = ["甜甜", "乔家劲", "肖冉", "赵海博", "韩一墨", "章晨泽", "李尚武", "林檎", "齐夏"]
        for i, name in enumerate(clockwise_order):
            if state.auto_stopped:
                break
            agent = _find_agent(name)
            if not agent:
                continue
            if name in state.manual_players:
                _wait_manual("story", name, f"讲述你的死亡故事（第{i+1}个发言）")
                story = await _await_manual_input()
            else:
                try:
                    story, _ = await _run_blocking(agent.tell_story, i + 1)
                except Exception:
                    story = "[待补充]"
            state.log(name, f"📖 {story}", "ai")
            # 每条故事间暂停让前端有时间渲染
            if state.auto_mode:
                await asyncio.sleep(1.5)
        state.log("系统", "所有故事讲完。开始自由讨论——找出说谎者！", "system")
        state.phase = "discussion"
        state.round_num = 1
        if not state.auto_stopped:
            await _run_freediscussion()
    elif action == "run_voting":
        await _run_voting_internal()
    elif action == "announce_result":
        _announce_result_internal()
    elif action == "next_cycle":
        state.current_cycle += 1
        was_awakened = [a.name for a in state.participants if a.player.awakened]
        state.reset_cycle()
        state.log("系统", f"═════ 第 {state.current_cycle} 轮回 ═════", "system")
        for agent in state.participants:
            if not agent.player.awakened:
                agent.memory = []
                agent.suspicion = {}
                agent.thoughts = []
            agent._system_prompt = agent._build_prompt()
        if state.current_cycle >= 2 and was_awakened:
            state.log("系统", "觉醒者在身份牌上看到了奇怪的字……", "system")
            for name in was_awakened:
                state.log("⚡ 回响", f"{name} 的卡牌上写着：「不要告诉任何人你还记得。」", "echo")
            state.log("系统", "卡牌上的字悄然变化，又变回了「说谎者」。", "system")
        intro = await _run_blocking(state.host.announce_game, [a.name for a in state.participants])
        state.log(f"🐑 {state.config.host_name}", f"[建议开场] {intro}", "speak")
        state.phase = "intro"
    elif action == "start_round":
        state.round_num += 1
        state.phase = "discussion"
        if not state.auto_stopped:
            await _run_freediscussion()


async def _run_freediscussion():
    """自由讨论 — 自然交锋"""
    state._discussion_active = True
    try:
        await _do_freediscussion()
    finally:
        state._discussion_active = False


async def _do_freediscussion():
    state.log("系统", f"═════ 第 {state.round_num} 轮自由讨论 ═════", "system")
    participants = list(state.participants)
    random.shuffle(participants)
    exchanges = min(5 + state.round_num * 2, 9)  # 讨论轮次越多越激烈
    for i in range(exchanges):
        if state.auto_paused or state.auto_stopped:
            break
        asker = participants[i % len(participants)]
        others = [a.name for a in participants if a.name != asker.name]
        if asker.name in state.manual_players:
            _wait_manual("question", asker.name, f"向谁提问？可选：{' '.join(others)}")
            manual_q = await _await_manual_input()
            # 解析格式：目标名 问题
            parts = manual_q.split(" ", 1)
            if len(parts) >= 2 and parts[0] in others:
                target_name = parts[0]
                question = parts[1]
            else:
                target_name = random.choice(others)
                question = manual_q
        else:
            try:
                target_name, question, _ = await _run_blocking(asker.ask_question, state.round_num, others)
            except Exception:
                target_name = random.choice(others)
                question = f"{target_name}，说说你的看法？"
        state.log(asker.name, f"→ {target_name}：{question}", "ai")
        respondent = _find_agent(target_name)
        if respondent:
            if target_name in state.manual_players:
                _wait_manual("answer", target_name, f"{asker.name}问你：{question}")
                answer = await _await_manual_input()
            else:
                try:
                    answer, _ = await _run_blocking(respondent.answer_question, state.round_num, asker.name, question)
                except Exception:
                    answer = "……让我想想。"
            state.log(respondent.name, f"← {answer}", "ai")
            qa = QARecord(round_num=state.round_num, asker=asker.name, respondent=respondent.name, question=question, answer=answer)
            state.all_qa.append(qa)
            for agent in state.participants:
                agent.observe(qa)
        if state.auto_mode:
            await asyncio.sleep(2 + random.random() * 1.5)
    # 人羊点评
    try:
        comment = await _run_blocking(state.host.comment, state.round_num, f"第{state.round_num}轮讨论激烈")
    except Exception:
        comment = f"第{state.round_num}轮结束了。怀疑在蔓延……"
    state.log(f"🐑 {state.config.host_name}", f"[点评] {comment}", "speak")
    if state.round_num < state.total_rounds:
        state.round_num += 1
        state.phase = "discussion"
        if state.auto_mode and not state.auto_paused and not state.auto_stopped:
            await asyncio.sleep(2)
            if not state.auto_paused and not state.auto_stopped:
                await _do_freediscussion()
    else:
        state.phase = "voting"
        if state.auto_mode and not state.auto_stopped:
            await _run_voting_internal()


async def _run_voting_internal():
    """内部投票逻辑"""
    state.phase = "voting"
    state.log("系统", "═════ 投票阶段 ═════", "system")
    all_names = [a.name for a in state.participants]
    vote_options = all_names + ["人羊"]
    state.votes = []
    for agent in state.participants:
        if agent.name in state.manual_players:
            _wait_manual("vote", agent.name, f"投票给谁？可选：{' '.join(vote_options)}")
            manual_vote = await _await_manual_input()
            parts = manual_vote.split(" ", 1)
            if parts[0] in vote_options:
                target = parts[0]
                reason = parts[1] if len(parts) > 1 else "玩家手动投票"
            else:
                target = random.choice(vote_options)
                reason = "手动输入解析失败"
        else:
            try:
                target, reason = await _run_blocking(agent.vote, 1, vote_options)
            except Exception:
                others = [n for n in all_names if n != agent.name]
                target = random.choice(others + ["人羊"]) if others else "人羊"
                reason = "随机选择"
        if target:
            vote = Vote(voter=agent.name, target=target, reason=reason)
            state.votes.append(vote)
            state.log(agent.name, f"投票给 {target}（{reason}）", "vote")
    vote_tally = {}
    for v in state.votes:
        vote_tally[v.target] = vote_tally.get(v.target, 0) + 1
    all_voted_host = all(v.target == "人羊" for v in state.votes)
    unanimous = len(set(v.target for v in state.votes)) == 1
    host_voted_out = unanimous and all_voted_host
    state.log("系统", f"投票统计：{json.dumps(vote_tally, ensure_ascii=False)}", "system")
    if host_voted_out:
        state.log("系统", "全员投票给了「人羊」——他们发现了真相！", "system")
    else:
        state.log("系统", "投票不统一——人羊的谎言未被完全识破。", "system")
    # 回响判定（基于思考过程，比公开发言更真实）
    state.awakening_results = []
    events_with_speakers = [{"content": e.get("content", ""), "speaker": e.get("speaker", "")} for e in state.dialog_log]
    for agent in state.participants:
        echo_name = agent.player.personality.echo.name if agent.player.personality.echo else None
        # 提取角色本轮思考过程作为觉醒判定核心依据
        thinking_text = "\n".join(t.get("thinking", "") for t in agent.thoughts if t.get("thinking"))
        result = state.echo_sys.check_awakening(agent.name, echo_name, events_with_speakers, state.current_cycle, thinking_text=thinking_text)
        state.awakening_results.append(result)
        if result.awakened:
            agent.player.awakened = True
            state.log("⚡ 回响", f"{agent.name} 觉醒了「{result.echo_name}」！", "echo")
            effect = state.echo_sys.get_echo_effect(agent.name)
            if effect:
                state.log("⚡ 回响", effect, "echo")
    if not any(r.awakened for r in state.awakening_results):
        state.log("系统", "无人觉醒回响。", "system")
    state.phase = "result_pending"
    if state.auto_mode and not state.auto_stopped:
        await asyncio.sleep(2)
        _announce_result_internal()


def _announce_result_internal():
    """内部宣布结果"""
    vote_tally = {}
    for v in state.votes:
        vote_tally[v.target] = vote_tally.get(v.target, 0) + 1
    all_voted_host = all(v.target == "人羊" for v in state.votes)
    unanimous = len(set(v.target for v in state.votes)) == 1
    host_voted_out = unanimous and all_voted_host
    if host_voted_out:
        state.log("🐑 人羊", "「……你们发现了。」", "host")
        state.log("系统", "人羊缓缓举起手枪，对准了自己的心脏。", "scene")
        state.log("系统", "砰——！一声枪响在封闭的房间中回荡。", "scene")
        state.log("系统", "人羊捂住了胸膛开始惨叫，鲜血从指缝中涌出。隔了几分钟，闷哼声也听不到了。", "scene")
        state.log("系统", "他死了。", "system")
        state.log("系统", "所有人发现自己的双腿可以使得上力气了。", "scene")
        state.log("系统", "乔家劲走上前，摘下了人羊的面具。面具内侧用黑色的钢笔写着字：", "scene")
        state.log("🐑 人羊(面具)", "「我是「人狗」。你们受了诅咒。我希望你们活下去。时钟一刻不停，四面皆有杀机。若想活下去，请往家乡的方向转动一百次。雨后春笋——为什么春笋不怕雨打？雨后见。」", "host")
    else:
        state.log("🐑 人羊", "「呵呵……看来你们还没明白。」", "host")
        state.log("系统", "人羊缓缓举起了手中的枪。", "scene")
        state.log("系统", "「规则是绝对的。你们选错了。」", "host")
        state.log("系统", "砰——", "scene")
        state.log("系统", "全员处决。人羊获胜。", "system")
    for r in state.awakening_results:
        if r.awakened and r.memories_retained:
            for mem in r.memories_retained:
                state.mem_mgr.add_memory(r.character_name, mem)
    non_awakened = [a.name for a in state.participants
                    if not any(r.awakened and r.character_name == a.name for r in state.awakening_results)]
    state.mem_mgr.wipe_non_awakened(non_awakened)
    state.phase = "result"
    if state.auto_mode and not state.auto_stopped:
        # auto loop 会处理 delay + next_cycle 过渡
        pass


@app.get("/", response_class=HTMLResponse)
def index():
    html_path = Path(__file__).parent / "templates" / "liar_web.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Template not found</h1>"


def _find_agent(name: str) -> Optional[ParticipantAgent]:
    for a in state.participants:
        if a.name == name:
            return a
    return None


def _make_actions(phase: str) -> list[dict]:
    if phase == "opening":
        return [
            {"label": "📖 朗读开场白（击杀第10人）", "action": "do_opening", "style": "btn-primary"},
        ]
    elif phase == "intro":
        return [
            {"label": "✅ 宣布规则，开始讲故事", "action": "use_intro", "style": "btn-primary"},
            {"label": "🔄 重新生成规则说明", "action": "regenerate_intro"},
        ]
    elif phase == "storytelling":
        return [{"label": "⏳ 故事生成中……", "action": "", "disabled": True}]
    elif phase == "storytold":
        return [
            {"label": "▶ 开始自由讨论", "action": "start_discussion", "style": "btn-primary"},
        ]
    elif phase == "discussion":
        return [{"label": "⏳ 讨论进行中……", "action": "", "disabled": True}]
    elif phase == "round_end":
        r = state.round_num
        if r < state.total_rounds:
            return [
                {"label": f"▶ 进入第 {r+1} 轮", "action": "start_round", "style": "btn-primary"},
            ]
        return [
            {"label": "🗳 进入投票阶段", "action": "run_voting", "style": "btn-primary"},
        ]
    elif phase == "voting":
        return [{"label": "🗳 进入投票阶段", "action": "run_voting", "style": "btn-primary"}]
    elif phase == "result_pending":
        return [{"label": "📢 宣布结果", "action": "announce_result", "style": "btn-primary"}]
    elif phase == "result":
        return [
            {"label": "🔄 下一轮回", "action": "next_cycle", "style": "btn-primary"},
            {"label": "🏁 结束游戏", "action": "end_game"},
        ]
    return []


# ── API: 创建游戏 ──

@app.post("/api/start")
async def api_start(req: Request):
    body = await req.json()
    state.config.total_players = 9
    state.config.liar_count = 9  # 原著版：所有人都是说谎者
    state.config.rounds = body.get("rounds", 2)
    state.config.host_name = "人羊"
    state.total_rounds = state.config.rounds
    # 齐夏用 V4-Pro，其余用 V4-Flash
    state.llm = LLMClient()
    flash_cfg = LLMConfig()
    flash_cfg.model = "deepseek-v4-flash"
    flash_llm = LLMClient(flash_cfg)

    all_chars = load_characters()
    total = state.config.total_players
    selected = random.sample(all_chars, min(total, len(all_chars)))
    random.shuffle(selected)

    state.players = []
    state.participants = []
    state.mem_mgr = MemoryManager()

    for persona in selected:
        # 原著版：所有参与者都是说谎者，但每人以为自己才是唯一那个
        player = Player(name=persona.name, personality=persona, role=Role.LIAR)
        llm = state.llm if persona.name == "齐夏" else flash_llm
        agent = ParticipantAgent(
            player=player, llm=llm, mem_mgr=state.mem_mgr,
            total_players=len(selected), liar_count=1,  # 每人认为只有1个说谎者
            total_rounds=state.config.rounds, host_name=state.config.host_name,
        )
        state.players.append(player)
        state.participants.append(agent)

    zodiac_data = pick_zodiac(state.config.host_name)
    if not zodiac_data:
        from game_engine import GameEngine
        zodiac_data = GameEngine()._default_host()
    state.host = ZodiacAgent(zodiac_data, state.llm)

    state.reset_cycle()
    state.phase = "opening"

    # 入场描述
    state.log("系统", "═ 终焉之地 · 说谎者 ═", "system")
    state.log("系统", "一个老旧的钨丝灯被黑色的电线悬在屋子中央，闪烁着昏暗的光芒。", "scene")
    state.log("系统", "房间的正中央放着一张大圆桌，斑驳不堪。桌子中央立着一尊小小的座钟，滴答作响。", "scene")
    state.log("系统", "围绕桌子一周，坐着十个衣着各异的人。他们有的趴在桌面上，有的仰坐在椅子上，沉沉睡着。", "scene")
    state.log("系统", "在这十人的身边，静静地站着一个戴着山羊头面具、身穿黑色西服的男人。", "scene")
    state.log("系统", "他的目光从破旧的山羊头面具里穿出，饶有兴趣地盯着十个人。", "scene")

    # 自动执行开场（击杀第10人 + 抽卡 + 宣布规则）
    await _exec_action("do_opening")

    return {
        "participants": [
            {"name": p.name,
             "echo": p.personality.echo.name if p.personality.echo else None,
             "is_liar": True,
             "org": p.personality.organization}
            for p in state.players
        ],
        "dialog": state.dialog_log[-15:],
        "actions": _make_actions(state.phase),
        "status": f"第{state.current_cycle}轮回 · {state.phase}阶段",
        "cycle": state.current_cycle,
        "round": state.round_num,
        "phase": state.phase,
        "host_name": state.config.host_name,
    }


# ── API: 动作 ──

@app.post("/api/action")
async def api_action(req: Request):
    body = await req.json()
    action = body.get("action", "")
    content = body.get("content", "")
    round_num = body.get("round_num", 0)

    if action == "do_opening":
        # 原著开场：第10人被击杀
        state.phase = "intro"
        state.log("系统", "座钟响了。分针与时针同时指向了「十二」。房间之外很遥远的地方，传来了低沉的钟声。", "scene")
        state.log("系统", "十个人慢慢苏醒了。他们迷惘地看了看四周，又疑惑地看了看对方。", "scene")
        state.log("🐑 人羊", "「早安，九位。」", "host")
        state.log("系统", "山羊头的声音从面具后传出，带着一股膻腥味。", "scene")
        state.log("系统", "乔家劲愣了几秒，带着犹豫开口：「你……是谁？」", "ai")
        state.log("🐑 人羊", "「相信你们都有这个疑问，那我就跟九位介绍一下。」", "host")
        state.log("🐑 人羊", "「我是「人羊」，而你们是「参与者」。如今把你们聚在一起，是为了参与一个游戏，最终创造一个「神」。」", "host")
        state.log("系统", "人羊缓缓来到一个年轻人身后。那年轻人脸上洋溢着诡异的微笑。", "scene")
        state.log("系统", "只听一声闷响——人羊把年轻人的头狠狠撞在了桌面上。", "scene")
        state.log("系统", "粉白色的东西如倾洒的颜料，在桌面上横向铺开。每个人的脸旁都溅到了血点。", "scene")
        state.log("系统", "年轻人的头颅在桌面上被撞了个粉碎。房间外，再次响起了一阵遥远的钟声。", "scene")
        state.log("系统", "坐在死者右边的女生面容扭曲，放声尖叫。", "ai")
        state.log("🐑 人羊", "「之所以准备了十个人，是为了用其中一人让你们安静下来。」", "host")
        state.log("系统", "人羊从裤子口袋中抽出一小叠卡片，那卡片看起来有扑克牌大小，背面写着「女娲游戏」四个字。", "scene")
        state.log("系统", "「下面，请大家抽卡。」人羊将卡片在桌面上摊开。", "host")
        state.log("系统", "九个人依次抽了一张卡。甜甜翻开卡面，手指微微颤抖。每个人的表情各异——有人皱眉，有人沉默，有人露出诡异的微笑。", "scene")
        state.log("系统", "人羊缓缓扫视众人：「你们当中，有且只有一个说谎者。抽到说谎者的人，必须在故事中掺杂谎言。」", "host")

        # 生成开场白建议
        intro = await _run_blocking(
            state.host.announce_game, [a.name for a in state.participants]
        )
        state.log(f"🐑 {state.config.host_name}", f"「{intro}」", "speak")

        return {
            "dialog": state.dialog_log[-20:],
            "actions": _make_actions("intro"),
            "status": "第10人已击杀。人羊，请宣布规则。",
            "cycle": state.current_cycle,
            "round": 0,
        }

    elif action == "use_intro":
        state.phase = "storytelling"
        state.round_num = 0
        state.log("系统", "═════ 讲故事阶段 ═════", "system")
        state.log("系统", "人羊宣布规则：「有且只有一个说谎者」。每人轮流讲述死亡故事，说谎者必须在故事中掺杂谎言。", "system")
        state.log("系统", "按顺序：甜甜→乔家劲→肖冉→赵海博→韩一墨→章晨泽→李尚武→林檎→齐夏。", "system")
        return await _run_storytelling()

    elif action == "regenerate_intro":
        intro = await _run_blocking(
            state.host.announce_game, [a.name for a in state.participants]
        )
        state.log(f"🐑 {state.config.host_name}", f"[新建议] {intro}", "speak")
        return {
            "dialog": state.dialog_log[-5:],
            "actions": _make_actions("intro"),
            "status": "新开场白已生成，请确认。",
        }

    elif action == "start_discussion":
        state.phase = "discussion"
        state.round_num = 1
        state.log("系统", f"═════ 第 {state.round_num} 轮讨论开始 ═════", "system")
        return await _run_discussion()

    elif action == "run_voting":
        return await _run_voting()

    elif action == "start_round":
        state.round_num += 1
        state.phase = "discussion"
        state.log("系统", f"═════ 第 {state.round_num} 轮讨论开始 ═════", "system")
        return await _run_discussion()

    elif action == "change_cycle":
        delta = body.get("delta", 0)
        state.current_cycle = max(1, state.current_cycle + delta)
        return {"status": f"轮回: {state.current_cycle}", "cycle": state.current_cycle}

    elif action == "change_round":
        delta = body.get("delta", 0)
        state.round_num = max(0, state.round_num + delta)
        return {"status": f"轮: {state.round_num}", "round": state.round_num}

    elif action == "silence":
        state.log(f"🐑 {state.config.host_name}", "「安静！」", "host")
        return {
            "dialog": state.dialog_log[-3:],
            "status": f"{state.config.host_name}让大家安静。",
            "actions": [],
        }

    elif action == "announce_result":
        return _announce_result()

    elif action == "next_cycle":
        return await _next_cycle()

    elif action == "end_game":
        state.log("系统", "游戏结束。终焉之地归于平静……", "system")
        return {"dialog": state.dialog_log[-3:], "actions": [], "status": "游戏已结束。"}

    elif action == "host_speak":
        if content:
            state.log(f"🐑 {state.config.host_name} (你)", content, "host")
        return {"dialog": state.dialog_log[-3:], "status": state.phase, "actions": []}

    return {"status": "unknown", "actions": []}


# ── API: 自动模式 ──

@app.post("/api/auto")
async def api_auto(req: Request):
    body = await req.json()
    action = body.get("action", "")
    if action == "start":
        state.auto_mode = True
        state.auto_paused = False
        state.auto_stopped = False
        if state._auto_task is None or state._auto_task.done():
            state._auto_task = asyncio.ensure_future(_auto_loop())
        return {"status": "auto_started", "auto_mode": True}
    elif action == "pause":
        state.auto_paused = True
        return {"status": "paused", "auto_mode": True}
    elif action == "resume":
        state.auto_paused = False
        return {"status": "resumed", "auto_mode": True}
    elif action == "stop":
        state.auto_stopped = True
        state.auto_mode = False
        return {"status": "stopped", "auto_mode": False}
    return {"status": "unknown"}


# ── 手动操控 ──

@app.post("/api/manual_toggle")
async def api_manual_toggle(req: Request):
    body = await req.json()
    name = body.get("name", "")
    if name in state.manual_players:
        state.manual_players.discard(name)
        return {"manual": False}
    else:
        state.manual_players.add(name)
        return {"manual": True}

@app.post("/api/manual_input")
async def api_manual_input(req: Request):
    body = await req.json()
    content = body.get("content", "")
    state.manual_input_data = content
    state.manual_event.set()
    # 立即将用户输入显示在对话中，提供视觉反馈
    if state.awaiting_manual:
        char_name = state.awaiting_manual.get("character", "")
        action_type = state.awaiting_manual.get("type", "speak")
        if action_type == "vote":
            state.log(char_name, f"投票：{content}", "vote")
        else:
            state.log(char_name, content, "ai")
    return {"status": "received"}


# ── 视角系统 ──

@app.post("/api/perspective")
async def api_perspective(req: Request):
    body = await req.json()
    name = body.get("name", "host")
    state.current_perspective = name
    return {"perspective": name}

@app.post("/api/character_auto")
async def api_character_auto(req: Request):
    body = await req.json()
    name = body.get("name", "")
    enabled = body.get("enabled", True)
    if enabled:
        state.character_auto[name] = True
    else:
        state.character_auto.pop(name, None)
    return {"character_auto": state.character_auto}


# ── AI 辅助 ──

@app.post("/api/ai_assist")
async def api_ai_assist(req: Request):
    """AI辅助：为手动操控的角色生成发言建议"""
    body = await req.json()
    name = body.get("name", "")
    context = body.get("context", "")  # 当前场景描述
    action_type = body.get("action_type", "speak")  # story/question/answer/vote

    agent = None
    for a in state.participants:
        if a.name == name:
            agent = a
            break
    if not agent:
        return {"suggestion": "（找不到角色）"}

    try:
        if action_type == "story":
            suggestion, _ = await _run_blocking(agent.tell_story, 0)
        elif action_type == "question":
            others = [a.name for a in state.participants if a.name != name]
            _, question, _ = await _run_blocking(agent.ask_question, state.round_num, others)
            suggestion = f"对某人说：{question}"
        elif action_type == "answer":
            answer, _ = await _run_blocking(agent.answer_question, state.round_num, "某人", context)
            suggestion = answer
        elif action_type == "vote":
            others = [a.name for a in state.participants]
            target, reason = await _run_blocking(agent.vote, 1, others + ["人羊"])
            suggestion = f"投票给 {target}（{reason}）"
        else:
            suggestion = context or "（请发言）"
        return {"suggestion": suggestion, "thinking": agent.thoughts[-1].get("thinking", "") if agent.thoughts else ""}
    except Exception as e:
        return {"suggestion": f"（AI辅助失败: {e}）"}


def _get_thoughts(character: str) -> list[dict]:
    """获取指定角色的思考记录"""
    if character == "host":
        return []
    for agent in state.participants:
        if agent.name == character:
            return agent.thoughts[-5:]  # 最近5条
    return []


def _wait_manual(action_type: str, character: str, context: str = ""):
    """标记等待手动输入，在 auto-flow 中 await"""
    state.awaiting_manual = {
        "type": action_type,
        "character": character,
        "context": context,
    }
    state.log("系统", f"✋ 等待你操控「{character}」发言……", "system")


async def _await_manual_input() -> str:
    """等待用户提交手动输入（可被 auto_stopped 中断）"""
    state.manual_event.clear()
    state.manual_input_data = ""
    while not state.auto_stopped:
        try:
            await asyncio.wait_for(state.manual_event.wait(), timeout=1.0)
            break
        except asyncio.TimeoutError:
            continue
    if state.auto_stopped:
        state.awaiting_manual = None
        return ""
    content = state.manual_input_data
    state.awaiting_manual = None
    state.manual_input_data = ""
    return content# ── 讲故事 ──

async def _run_storytelling() -> dict:
    clockwise_order = ["甜甜", "乔家劲", "肖冉", "赵海博", "韩一墨", "章晨泽", "李尚武", "林檎", "齐夏"]

    for i, name in enumerate(clockwise_order):
        agent = _find_agent(name)
        if not agent:
            continue
        try:
            story, _ = await _run_blocking(agent.tell_story, i + 1)
        except Exception:
            story = "[待补充]"
        state.log(name, f"📖 {story}", "ai")

    state.log("系统", "所有故事讲完。开始自由讨论——找出说谎者！", "system")
    state.phase = "storytold"

    # 自动进入讨论阶段
    state.round_num = 1
    state.phase = "discussion"
    state.log("系统", f"═════ 第 {state.round_num} 轮自由讨论开始 ═════", "system")
    return await _run_discussion()


# ── 讨论 ──

async def _run_discussion() -> dict:
    r = state.round_num
    order = list(range(len(state.participants)))
    random.shuffle(order)
    order = order[:7]  # 每轮7人发言，更深入的讨论

    for idx in order:
        asker = state.participants[idx]
        others = [a.name for a in state.participants if a.name != asker.name]

        try:
            target_name, question, _ = await _run_blocking(
                asker.ask_question, r, others
            )
        except Exception:
            target_name = random.choice(others)
            question = f"{target_name}，说说你的看法？"

        state.log(asker.name, f"→ {target_name}：{question}", "ai")

        respondent = _find_agent(target_name)
        if respondent:
            try:
                answer, _ = await _run_blocking(
                    respondent.answer_question, r, asker.name, question
                )
            except Exception:
                answer = "……让我想想。"
            state.log(respondent.name, f"← {answer}", "ai")

            qa = QARecord(round_num=r, asker=asker.name, respondent=respondent.name, question=question, answer=answer)
            state.all_qa.append(qa)
            for agent in state.participants:
                agent.observe(qa)

    try:
        comment = await _run_blocking(state.host.comment, r, f"第{r}轮讨论中出现了一些有趣的交锋")
    except Exception:
        comment = f"第{r}轮结束了。怀疑在蔓延……"
    state.log(f"🐑 {state.config.host_name}", f"[点评] {comment}", "speak")

    phase = "round_end" if r < state.total_rounds else "voting"
    state.phase = phase
    status = f"第{r}轮完成。人羊，请决定下一步。" if r < state.total_rounds else "讨论结束。请进入投票阶段——目标可以是参与者，也可以是人羊。"

    return {
        "dialog": state.dialog_log[-30:],
        "actions": _make_actions(phase),
        "status": status,
        "cycle": state.current_cycle,
        "round": r,
    }


# ── 投票 ──

async def _run_voting() -> dict:
    state.phase = "voting"
    state.log("系统", "═════ 投票阶段 ═════", "system")

    all_names = [a.name for a in state.participants]
    vote_options = all_names + ["人羊"]  # 可投票给人羊（但系统不提示）
    state.votes = []

    for agent in state.participants:
        if agent.name in state.manual_players:
            _wait_manual("vote", agent.name, f"投票给谁？可选：{' '.join(vote_options)}")
            manual_vote = await _await_manual_input()
            parts = manual_vote.split(" ", 1)
            if parts[0] in vote_options:
                target = parts[0]
                reason = parts[1] if len(parts) > 1 else "玩家手动投票"
            else:
                target = random.choice(vote_options)
                reason = "手动输入解析失败"
        else:
            try:
                target, reason = await _run_blocking(agent.vote, 1, vote_options)
            except Exception:
                others = [n for n in all_names if n != agent.name]
                target = random.choice(others + ["人羊"]) if others else "人羊"
                reason = "随机选择"

        if target:
            vote = Vote(voter=agent.name, target=target, reason=reason)
            state.votes.append(vote)
            state.log(agent.name, f"投票给 {target}（{reason}）", "vote")

    # 统计票数
    vote_tally = {}
    for v in state.votes:
        vote_tally[v.target] = vote_tally.get(v.target, 0) + 1

    # 原著版胜败判定：必须全员投票给人羊才赢，否则全员死亡
    all_voted_host = all(v.target == "人羊" for v in state.votes)
    unanimous = len(set(v.target for v in state.votes)) == 1
    host_voted_out = unanimous and all_voted_host

    state.log("系统", f"投票统计：{json.dumps(vote_tally, ensure_ascii=False)}", "system")
    if host_voted_out:
        state.log("系统", "全员投票给了「人羊」——他们发现了真相！", "system")
    else:
        state.log("系统", "投票不统一——人羊的谎言未被完全识破。", "system")

    # 回响判定（基于思考过程，比公开发言更真实）
    state.awakening_results = []
    events_with_speakers = [{"content": e.get("content", ""), "speaker": e.get("speaker", "")} for e in state.dialog_log]
    for agent in state.participants:
        echo_name = agent.player.personality.echo.name if agent.player.personality.echo else None
        # 提取角色本轮思考过程作为觉醒判定核心依据
        thinking_text = "\n".join(t.get("thinking", "") for t in agent.thoughts if t.get("thinking"))
        result = state.echo_sys.check_awakening(agent.name, echo_name, events_with_speakers, state.current_cycle, thinking_text=thinking_text)
        state.awakening_results.append(result)
        if result.awakened:
            agent.player.awakened = True
            state.log("⚡ 回响", f"{agent.name} 觉醒了「{result.echo_name}」！", "echo")
            effect = state.echo_sys.get_echo_effect(agent.name)
            if effect:
                state.log("⚡ 回响", effect, "echo")

    if not any(r.awakened for r in state.awakening_results):
        state.log("系统", "无人觉醒回响。", "system")

    state.phase = "result_pending"

    return {
        "dialog": state.dialog_log[-40:],
        "actions": _make_actions("result_pending"),
        "status": "投票完成。人羊，请宣布结果。",
        "cycle": state.current_cycle,
        "round": state.round_num,
        "vote_tally": vote_tally,
        "host_voted_out": host_voted_out,
    }


# ── 宣布结果 ──

def _announce_result() -> dict:
    vote_tally = {}
    for v in state.votes:
        vote_tally[v.target] = vote_tally.get(v.target, 0) + 1

    # 判断是否全员投票给人羊
    all_voted_host = all(v.target == "人羊" for v in state.votes)
    unanimous = len(set(v.target for v in state.votes)) == 1
    host_voted_out = unanimous and all_voted_host

    if host_voted_out:
        # 原著：全员投票给人羊——人羊自杀
        state.log("🐑 人羊", "「……你们发现了。」", "host")
        state.log("系统", "人羊缓缓举起手枪，对准了自己的心脏。", "scene")
        state.log("系统", "砰——！一声枪响在封闭的房间中回荡。", "scene")
        state.log("系统", "人羊捂住了胸膛开始惨叫，鲜血从指缝中涌出。隔了几分钟，闷哼声也听不到了。", "scene")
        state.log("系统", "他死了。", "system")
        state.log("系统", "所有人发现自己的双腿可以使得上力气了。", "scene")

        # 面具下的文字
        state.log("系统", "乔家劲走上前，摘下了人羊的面具。面具内侧用黑色的钢笔写着字：", "scene")
        state.log("🐑 人羊(面具)", "「我是「人狗」。你们受了诅咒。我希望你们活下去。时钟一刻不停，四面皆有杀机。若想活下去，请往家乡的方向转动一百次。雨后春笋——为什么春笋不怕雨打？雨后见。」", "host")

        winner = "众人"
        state.phase = "result"
    else:
        # 投票不统一——全员死亡
        state.log("🐑 人羊", "「呵呵……看来你们还没明白。」", "host")
        state.log("系统", "人羊缓缓举起了手中的枪。", "scene")
        state.log("系统", "「规则是绝对的。你们选错了。」", "host")
        state.log("系统", "砰——", "scene")
        state.log("系统", "全员处决。人羊获胜。", "system")
        winner = "人羊"
        state.phase = "result"

    for r in state.awakening_results:
        if r.awakened and r.memories_retained:
            for mem in r.memories_retained:
                state.mem_mgr.add_memory(r.character_name, mem)

    non_awakened = [a.name for a in state.participants
                    if not any(r.awakened and r.character_name == a.name for r in state.awakening_results)]
    state.mem_mgr.wipe_non_awakened(non_awakened)

    return {
        "dialog": state.dialog_log[-15:],
        "actions": _make_actions("result"),
        "status": f"{'众人获胜！人羊已死。面具下另有玄机……' if host_voted_out else '全员死亡。人羊获胜。'}",
        "cycle": state.current_cycle,
        "round": state.round_num,
        "winner": winner,
        "host_voted_out": host_voted_out,
    }


# ── 下一轮回 ──

async def _next_cycle() -> dict:
    state.current_cycle += 1
    was_awakened = [a.name for a in state.participants if a.player.awakened]
    state.reset_cycle()
    state.log("系统", f"═════ 第 {state.current_cycle} 轮回 ═════", "system")

    for agent in state.participants:
        if not agent.player.awakened:
            agent.memory = []
            agent.suspicion = {}
            agent.thoughts = []
        agent._system_prompt = agent._build_prompt()

    # 第二轮以上：觉醒者收到人羊的密信
    if state.current_cycle >= 2 and was_awakened:
        state.log("系统", "觉醒者在身份牌上看到了奇怪的字……", "system")
        for name in was_awakened:
            state.log("⚡ 回响", f"{name} 的卡牌上写着：「不要告诉任何人你还记得。」", "echo")
        state.log("系统", "卡牌上的字悄然变化，又变回了「说谎者」。", "system")

    intro = await _run_blocking(
        state.host.announce_game, [a.name for a in state.participants]
    )
    state.log(f"🐑 {state.config.host_name}", f"[建议开场] {intro}", "speak")

    return {
        "dialog": state.dialog_log[-5:],
        "actions": _make_actions("intro"),
        "status": f"第 {state.current_cycle} 轮回！人羊请开场。",
        "cycle": state.current_cycle,
        "round": 0,
    }


# ── 状态 ──

@app.get("/api/state")
def get_state():
    awakened = [r.character_name for r in state.awakening_results if r.awakened]
    return {
        "dialog": state.dialog_log[-50:],
        "phase": state.phase,
        "status": f"{getattr(state.config, 'host_name', '人羊')} | 第{state.current_cycle}轮回 | 第{state.round_num}轮",
        "cycle": state.current_cycle,
        "round": state.round_num,
        "awakened": awakened,
        "actions": _make_actions(state.phase),
        "elapsed": int(state.total_words / 80 * 60) if state.total_words > 0 else 0,
        "total_words": state.total_words,
        "auto_mode": state.auto_mode,
        "auto_paused": state.auto_paused,
        "manual_players": list(state.manual_players),
        "awaiting_manual": state.awaiting_manual,
        "current_perspective": state.current_perspective,
        "character_auto": state.character_auto,
        "character_thoughts": _get_thoughts(state.current_perspective) if state.current_perspective != "host" else [],
        "participant_names": [a.name for a in state.participants],
    }

@app.get("/api/export")
def export_dialog():
    """导出完整对话记录为文本文件"""
    lines = []
    lines.append("=" * 60)
    lines.append("  说谎者 · 终焉之地 — 完整对话记录")
    lines.append(f"  轮回: {state.current_cycle}  轮次: {state.round_num}")
    lines.append(f"  导出时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    for entry in state.dialog_log:
        t = entry.get("timestamp", "")
        s = entry.get("speaker", "")
        c = entry.get("content", "")
        lines.append(f"[{t}] {s}")
        lines.append(f"  {c}")
        lines.append("")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines), media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=liar_game_dialog_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8910, log_level="info")

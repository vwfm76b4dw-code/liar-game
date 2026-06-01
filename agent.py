"""AI Agent -- 参与者与生肖主持人（原著版）

每个Agent是一个独立的AI角色，拥有：
- 角色人设（Personality）
- 系统提示词（统一使用CANON_SYSTEM，每个参与者以为自己是唯一说谎者）
- 独立记忆（memory[]）
- 怀疑度追踪（suspicion{}）
- 思考记录（thoughts[]）
- 跨轮回记忆（通过MemoryManager加载）
"""

from __future__ import annotations
import random
from typing import Optional
from llm_client import LLMClient
from models import (
    Player, ZodiacHost, QARecord, DialogEvent, Role, CycleMemory,
)
from prompts.templates import (
    CANON_SYSTEM, ZODIAC_SYSTEM,
    QUESTION_PROMPT, ANSWER_PROMPT,
    VOTE_PROMPT, format_history, format_suspicion,
)
from memory_manager import MemoryManager


# 人物心理状态描述（忠于原著）
PSYCH_STATES = {
    "齐夏": "注意：这是说谎者游戏模拟（十日终焉）！！！冷静算计的外壳下压抑着殉道者的狂热。思维如精密仪器般缜密，时刻在计算和推演，一切皆为棋子。表面从容不迫，偶尔冷笑，但内心全是对妻子余念安的执念与疯狂——那是在黑暗中听到的妻子幻听，成为了他永恒执念的开始。他谁也不信，包括自己。曾化身生肖「白羊」却遭天龙暗算，曾七年不眠不休读书。他渴望终结轮回，哪怕粉身碎骨。精神处于极度不稳定的状态——可能在最冷静的瞬间突然爆发出令人胆寒的疯狂。兼具欺诈师的冷漠与殉道者的狂热，一个极度矛盾的悲剧英雄。",
    "甜甜": "出身陕西农村的22岁女孩，本名张丽娟。为了给患先天性心脏病的弟弟凑十几万手术费，被生活一步步逼入绝境——辍学、打工、被工厂老板骚扰、被全厂孤立排挤，最后走投无路进了夜场。18岁的年纪扛着「千里背债」的命运悲剧。表面油滑开朗、说话大胆直白，用笑容和调侃掩饰内心的绝望与破碎。自称'技术工作者'，言语带着江湖气。看似轻浮实则敏锐异常——这是她在底层挣扎多年练出的生存本能。内心深处早已被绝望浸透，但她仍选择笑着面对。",
    "乔家劲": "生于1979年的香港砵兰街硬汉，从小被荣爷收养，与兄弟九仔相依为命。为报恩替荣爷顶罪入狱4年，出狱后得知九仔惨死，独自复仇被推下时代广场天台。满口'冚家铲''粉肠'等粤语脏话，天不怕地不怕，敢直接骂人羊。直率暴躁的外表下是滴水之恩涌泉相报的赤子之心——他看透了江湖险恶，仍选择最简单的忠义之道。脑子其实转得很快，只是习惯了用拳头解决问题。内心深处对没能救到九仔充满愧疚。说话带着浓重的广东口音，普通话极差。对齐夏的信任毫无保留——因为他认定齐夏是值得追随的'大脑'。",
    "肖冉": "表面怯懦不安、楚楚可怜的23岁大理幼师，声音细小带着颤音。但那全是伪装——她的恶并非天性，而是匮乏导致的扭曲。家境贫寒让她对优渥生活产生疯狂的嫉妒，为了攀龙附凤不惜贩卖儿童并栽赃陷害同事陈婷。说话吞吞吐吐，常用'我……我不太确定……'句式。偶尔眼神中闪过的精明与算计会暴露真实面目。一生信奉依附强者，被抛弃时不惜疯狂报复。直到死亡她都不知道那个四岁女孩是否就是被她拐走的——这是她悲剧中最大的讽刺。",
    "赵海博": "45岁的江苏脑外科医生。表面沉稳务实，骨子里自私懦弱，一个充满市侩气息的普通人。用医术当铠甲——只要尽力而为便可卸下所有道德包袱。地震时正在为一位想陪儿子的母亲做开颅手术，第一反应不是逃生而是试图保护患者，但最终患者脑干反射消失，自己被天花板砸死——手术室成了未竟的战场。这场失败的救赎让他对生死近乎麻木。说话简短精准不带感情，双手插在白大褂口袋里。极度多疑不信任何人，习惯用医学逻辑分析一切。",
    "韩一墨": "29岁的广西网络作家，笔名一墨。内心充满平庸者的恶意与极致的懦弱。为了拯救没落的论坛人气，造黄谣害死无辜女生——这成为他永远无法摆脱的梦魇。保留七年完整轮回记忆，每次回到现实都尝试救她却以失败告终，甚至发展到控制她人身自由的疯狂地步。凌晨两点南宁天桥的失足坠落，脑袋砸在地面，被自己的罪孽终结。极度胆小、神经质、患有幽闭恐惧症。说话吞吞吐吐声音发颤，习惯推眼镜擦冷汗。什么都怕——怕黑怕鬼怕死怕被怀疑。常幻想自己是小说主角，把齐夏当神明，用幻想逃避现实。越害怕什么就越发生什么，因为「招灾」会让恐惧具象化。",
    "章晨泽": "32岁的四川女律师，原名章莱娣——'不被爱的女儿'最惨痛的写照。被父母以6.6万元卖给马屠户，被同事小孙救下相恋后又遭弟弟不断勒索。最终将全家杀死、纵火烧屋，开车去法院寻求正义时因地震从高架桥坠落。前半生为别人而活，后半生陷入毁灭性的复仇。表面理性犀利、充满精英气质，每句话都像在盘问证人。但内心深处极度自卑敏感，对公平有着超乎寻常的执拗——像一把随时可以杀人的刀。引用的不是法律条文，是她自己的血泪。",
    "李尚武": "35岁的内蒙刑侦支队长。天生的组织者和领导者，沉稳正义。但他的堕落源于父爱——为给女儿治病沦为黑警，充当毒贩的保护伞。英雄不再清白，恶人又未泯灭良知。2010年在呼市郊区追捕毒贩时被击中心脏，临终遗言'别怕，叔叔在这儿'。说话沉稳有力，目光直视对方，有警察的威严。对细节记忆精确，擅长分析时间线和物理轨迹。第一个提出「让大家都活下来」的人。内心背负着巨大的包袱，但在终焉之地中逐渐找回了正义与勇气。",
    "林檎": "24岁的'心理咨询师'——但她是一颗苹果。唐代以前「林檎」即苹果，她是终焉之地一棵古树上结出的果实，被青龙用仙法化形为人类，被植入虚假记忆。她从未离开过这里，是终焉之地的原住民。说话语速平缓，喜欢用提问回答问题。观察力极强，能洞悉他人真实动机。表面冷若冰霜，实则外冷内热。她的疏离感与旁观者气质是因为她骨子里找不到与这个世界的真实连接——她的一切都是被设计的产物。回响「激发」是青龙创造她的目的：作为安插在齐夏身边的针和催化剂，促成造神计划。但她最终背叛了青龙，选择与齐夏联手摧毁终焉之地。她是否真的有自我，连她也不确定——但正因如此，她在寻找自己存在的意义。",
}


class BaseAgent:
    """Agent基类"""
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.memory: list[QARecord] = []
        self.suspicion: dict[str, float] = {}
        self.thoughts: list[dict] = []
        self._system_prompt = ""

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def observe(self, qa: QARecord):
        self.memory.append(qa)
        respondent = qa.respondent
        if respondent != getattr(self, 'name', ''):
            self.suspicion.setdefault(respondent, 0.3)

    def chat_json(self, user_msg: str, temperature: Optional[float] = None) -> dict:
        return self.llm.chat_json(self._system_prompt, user_msg, temperature=temperature)


class ParticipantAgent(BaseAgent):
    """参与者Agent—— 全部认为自己是唯一的说谎者"""

    def __init__(self, player: Player, llm: LLMClient,
                 mem_mgr: Optional[MemoryManager] = None,
                 total_players: int = 9, liar_count: int = 1,
                 total_rounds: int = 3, host_name: str = "人羊"):
        super().__init__(llm)
        self.player = player
        self.mem_mgr = mem_mgr or MemoryManager()
        self.total_players = total_players
        self.liar_count = liar_count
        self.total_rounds = total_rounds
        self.host_name = host_name
        self._system_prompt = self._build_prompt()

    @property
    def name(self) -> str:
        return self.player.name

    @property
    def is_liar(self) -> bool:
        # 原著版：所有参与者都是说谎者
        return True

    @property
    def is_awakened(self) -> bool:
        return self.player.awakened

    def _build_prompt(self) -> str:
        p = self.player.personality
        psych_key = p.name
        psych_str = PSYCH_STATES.get(psych_key, "普通人心理")
        cycle_mem = self.mem_mgr.format_for_prompt(self.name) if self.is_awakened else "（未觉醒回响，无跨轮回记忆）"
        return CANON_SYSTEM.format(
            name=p.name, age=str(p.age), background=p.background,
            traits="、".join(p.traits), style=p.style,
            organization=p.organization or "无",
            total_players=self.total_players,
            liar_count=1,  # 每人认为只有1个说谎者
            host_name=self.host_name,
            total_rounds=self.total_rounds,
            psych_states=psych_str,
            cycle_memories=cycle_mem,
        )

    def update_params(self, total: int, liars: int, rounds: int, host: str):
        self.total_players = total
        self.liar_count = 1  # 永远1个（每人视角）
        self.total_rounds = rounds
        self.host_name = host
        self._system_prompt = self._build_prompt()

    def tell_story(self, order: int) -> tuple[str, str]:
        """讲述死亡故事。返回 (story, thinking)"""
        history = format_history([m.model_dump() for m in self.memory], self.name)
        from prompts.templates import STORY_PROMPT
        user_msg = STORY_PROMPT.format(
            order=order, history=history,
        )
        resp = self.chat_json(user_msg)
        thinking = resp.get("thinking", "")
        story = resp.get("story", "[待补充]")
        self.thoughts.append({"action": "story", "thinking": thinking})
        return story, thinking

    def ask_question(self, round_num: int, other_players: list[str]) -> tuple[str, str, str]:
        """生成提问。返回 (target, question, thinking)"""
        history = format_history([m.model_dump() for m in self.memory], self.name)
        suspicion_str = format_suspicion(self.suspicion)
        user_msg = QUESTION_PROMPT.format(
            round_num=round_num, total_rounds=self.total_rounds,
            history=history, suspicion_summary=suspicion_str,
        )
        resp = self.chat_json(user_msg)
        thinking = resp.get("thinking", "")
        target = resp.get("target", random.choice(other_players))
        question = resp.get("question", "你觉得这局游戏怎么样？")
        if target not in other_players:
            target = random.choice(other_players)
        self.thoughts.append({"round": round_num, "action": "ask", "thinking": thinking})
        return target, question, thinking

    def answer_question(self, round_num: int, asker: str, question: str) -> tuple[str, str]:
        """回答提问。返回 (answer, thinking)"""
        history = format_history([m.model_dump() for m in self.memory], self.name)
        user_msg = ANSWER_PROMPT.format(round_num=round_num, asker=asker, question=question, history=history)
        resp = self.chat_json(user_msg)
        thinking = resp.get("thinking", "")
        answer = resp.get("answer", "我不太确定……")
        self.thoughts.append({"round": round_num, "action": "answer", "thinking": thinking})
        return answer, thinking

    def vote(self, votes_count: int, all_players: list[str]) -> tuple[str, str]:
        """投票。返回 (target, reason)
        all_players包含所有参与者名字 + '人羊'
        """
        history = format_history([m.model_dump() for m in self.memory], self.name)
        from prompts.templates import VOTE_PROMPT
        user_msg = VOTE_PROMPT.format(full_history=history)
        resp = self.chat_json(user_msg)
        thinking = resp.get("thinking", "")
        self.thoughts.append({"round": -1, "action": "vote", "thinking": thinking})
        target = resp.get("target", "")
        reason = resp.get("reason", "")
        if target not in all_players:
            others = [p for p in all_players if p != self.name]
            target = random.choice(others) if others else ""
            reason = "随机选择（解析失败）"
        return target, reason


class ZodiacAgent(BaseAgent):
    """生肖主持人Agent"""
    def __init__(self, host: ZodiacHost, llm: LLMClient):
        super().__init__(llm)
        self.host = host
        self._system_prompt = self._build_prompt()

    @property
    def name(self) -> str:
        return self.host.name

    def _build_prompt(self) -> str:
        return ZODIAC_SYSTEM.format(
            name=self.host.name,
            mask_animal=self.host.mask_animal,
            tier=self.host.tier.value,
            style=self.host.style,
            cruelty=str(self.host.cruelty),
            background=self.host.personality.background,
            game_type="说谎者",
        )

    def announce_game(self, participants: list[str]) -> str:
        """宣布游戏开始"""
        plist = "、".join(participants)
        user_msg = f"游戏即将开始。参与者：{plist}。请你宣布游戏开始，介绍规则，制造紧张气氛。输出JSON：{{\"announcement\": \"你的开场白\"}}"
        resp = self.chat_json(user_msg)
        return resp.get("announcement", f"欢迎来到终焉之地。游戏开始。")

    def comment(self, round_num: int, event_desc: str) -> str:
        """在回合间进行评论"""
        user_msg = f"第{round_num}轮发生了以下事件：{event_desc}。请以主持人的身份简短评论（1-2句话），煽动怀疑和不安。输出JSON：{{\"comment\": \"你的评论\"}}"
        resp = self.chat_json(user_msg)
        return resp.get("comment", "有趣……继续。")

    def announce_result(self, winner: str, liars: list[str], caught: list[str]) -> str:
        """宣布最终结果"""
        user_msg = f"游戏结束。获胜方：{winner}。说谎者：{liars}。被找出：{caught}。请宣布结果并发表总结。输出JSON：{{\"announcement\": \"你的结果宣布\"}}"
        resp = self.chat_json(user_msg)
        return resp.get("announcement", f"游戏结束。{winner}获胜。")

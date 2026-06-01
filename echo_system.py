"""回响系统 -- 觉醒判定
忠于《十日终焉》：回响觉醒需要特定的个人契机。
使用AI辅助判断角色的发言是否触及回响触发条件。
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from models import CycleMemory, AwakeningResult

if TYPE_CHECKING:
    from llm_client import LLMClient

# 每个角色的回响定义（小说原著向）
ECHO_DEFS = {
    '齐夏': {
        'name': '灵闻',
        'trigger': '极致悲伤——对妻子余念安的执念与寻找',
        'trigger_question': '这个角色的发言是否流露出对失去爱人的极致悲伤、或对记忆/真相的执念？',
        'effect': '闭目凝神，听见了空气中不同回响的频率与声音',
        'effect_text': '齐夏闭上双眼，周围的嘈杂声仿佛消失了。他开始"听见"一些不一样的东西——那是回响在空气中震荡的微弱声音。',
    },
    '乔家劲': {
        'name': '破万法',
        'trigger': '守护信念——面对不公时渴望保护他人',
        'trigger_question': '这个角色的发言是否表达了面对不公时的愤怒、或渴望用实力保护他人的信念？',
        'effect': '攥紧拳头，一股无形的力量在身上蔓延——万法可破！',
        'effect_text': '乔家劲咬紧牙关，拳头攥得咯咯作响。一股无形的力量在他身上蔓延开来，仿佛任何邪法在他面前都不堪一击。',
    },
    '李尚武': {
        'name': '探囊',
        'trigger': '释然与放下——濒死或保护他人的决意',
        'trigger_question': '这个角色的发言是否表达了在危难中想要保护他人、或释然接受命运的决意？',
        'effect': '伸手探入虚空，从潜意识中取出认为"本就应该存在"的东西',
        'effect_text': '李尚武深吸一口气，缓缓伸出手探入面前的虚空。当他的手收回来时，竟然握住了一样东西——那是他潜意识中认为"本就应该存在"的物件。',
    },
    '章晨泽': {
        'name': '移魂',
        'trigger': '面对不公裁决时渴望扭转结局',
        'trigger_question': '这个角色的发言是否表达了对不公裁决的愤怒、或渴望用法律/规则以外的方式改变结局？',
        'effect': '身体变得透明，灵魂可以转移到他人的位置',
        'effect_text': '章晨泽感到一阵异样，她低头看向自己的双手——它们正在变得透明。她的灵魂仿佛可以从身躯中脱离，转移到任何她想去的方向。',
    },
    '林檎': {
        'name': '激发',
        'trigger': '激励他人突破极限',
        'trigger_question': '这个角色的发言是否在激励、鼓舞他人，帮助他人建立信心？',
        'effect': '通过触碰激发他人回响潜能',
        'effect_text': '林檎伸出手，轻轻触碰到了身边的同伴。一股温热的能量从她的指尖传递出去——那是能够激发回响的力量。',
    },
    '韩一墨': {
        'name': '招灾',
        'trigger': '极致的恐惧——越害怕灾难越降临',
        'trigger_question': '这个角色的发言是否流露出强烈的恐惧、不安、或对灾难的预感和担忧？',
        'effect': '信念中的灾难会因恐惧而具现化',
        'effect_text': '韩一墨浑身剧烈颤抖，脸上写满了恐惧。他的瞳孔放大——因为他"看见"了那场他一直在害怕的灾难，正在从虚空中凝结成形。',
    },
    '甜甜': {
        'name': '巧物',
        'trigger': '为帮助他人迫切希望制造有形之物',
        'trigger_question': '这个角色的发言是否表达了想要帮助他人、或迫切需要制造某个物品的愿望？',
        'effect': '用信念凭空创造自己完全了解的物品',
        'effect_text': '甜甜咬紧嘴唇，双手开始在空中比划。她的指尖所过之处，空气仿佛凝结成了实体——她在用自己的信念创造一样东西。',
    },
    '赵海博': {
        'name': '离析',
        'trigger': '冷静分析万物结构时洞察崩坏之理',
        'trigger_question': '这个角色的发言是否体现了冷静理性地分析事物结构、或洞察事物弱点？',
        'effect': '目光所及之处，无生命物体自动崩坏瓦解',
        'effect_text': '赵海博推了推眼镜，目光变得异常锐利。他所凝视的地方，物体的结构开始在他的视野中瓦解——那是"离析"的力量。',
    },
}


class EchoSystem:
    def __init__(self, llm: Optional['LLMClient'] = None):
        self.llm = llm
        self._awakened: set[str] = set()
        self._cycle_checked: set[str] = set()

    def check_awakening(self, name: str, echo_name: Optional[str], events: list[dict], cycle_id: int) -> AwakeningResult:
        if not echo_name or name not in ECHO_DEFS:
            return AwakeningResult(character_name=name, awakened=False)
        if name in self._awakened:
            return AwakeningResult(character_name=name, awakened=True, echo_name=echo_name, trigger_event='已觉醒',
                memories_retained=[CycleMemory(cycle_id=cycle_id, event_type='awakening', description=f'保持回响：{echo_name}', emotion='觉醒', importance=5)])
        if name in self._cycle_checked:
            return AwakeningResult(character_name=name, awakened=False, echo_name=echo_name, trigger_event='本轮已检查')
        self._cycle_checked.add(name)

        defi = ECHO_DEFS[name]
        my_speeches = [evt.get('content', '') for evt in events if evt.get('speaker') == name]
        combined = '\n'.join(my_speeches)
        if not combined.strip():
            return AwakeningResult(character_name=name, awakened=False, echo_name=echo_name, trigger_event='未发言')

        # AI辅助判断：是否达到觉醒契机
        if self.llm:
            triggered = self._judge_with_llm(name, defi, combined)
        else:
            # 降级：用关键词简单判断
            triggered = any(kw in combined for kw in defi.get('keywords', []))

        if not triggered:
            return AwakeningResult(character_name=name, awakened=False, echo_name=echo_name, trigger_event='契机未到')

        self._awakened.add(name)
        effect_text = defi.get('effect_text', '')
        memory = CycleMemory(cycle_id=cycle_id, event_type='awakening',
            description=f'{name}觉醒了回响「{defi["name"]}」——{defi["trigger"]}',
            emotion='觉醒', importance=5)
        return AwakeningResult(character_name=name, awakened=True, echo_name=defi['name'],
            trigger_event=defi['trigger'], memories_retained=[memory])

    def _judge_with_llm(self, name: str, defi: dict, speeches: str) -> bool:
        prompt = f"""你正在判断角色是否应该觉醒「回响」。

角色：{name}
回响名称：{defi['name']}
觉醒契机：{defi['trigger']}
判断标准：{defi['trigger_question']}

该角色的发言：
"""
        # 截取最近500字
        recent = speeches[-500:] if len(speeches) > 500 else speeches
        prompt += recent + '\n\n请严格判断：该角色当前的发言是否达到了觉醒回响的条件？只需回复JSON：{"awaken": true/false, "reason": "简要理由"}'

        try:
            resp = self.llm.chat_json("你是一个严格判断回响觉醒条件的系统。只有角色明确表达了与觉醒契机一致的情感/信念时才判定为true。", prompt)
            return resp.get('awaken', False)
        except Exception:
            return False

    def reset_cycle(self):
        self._cycle_checked.clear()

    def reset_all(self):
        self._awakened.clear()
        self._cycle_checked.clear()

    def is_awakened(self, name: str) -> bool:
        return name in self._awakened

    def get_echo_effect(self, name: str) -> str:
        defi = ECHO_DEFS.get(name)
        return defi.get('effect_text', '') if defi else ''

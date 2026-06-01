"""游戏输出 — JSON/Markdown双格式

使用 Rich 库进行终端美化输出，同时记录结构化JSON日志。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.text import Text

from models import GameResult, Role

console = Console()
_json_buffer: list[dict] = []


# ═══════════════════════════════════════════════════
# 游戏界面
# ═══════════════════════════════════════════════════

def show_banner(cycle: int, config):
    """游戏开始横幅"""
    md = f"""# 🎭 说谎者 — 终焉之地

> 第 **{cycle}** 轮回 | 主持人：{config.host_name}

- 参与者：{config.total_players} 人
- 说谎者：{config.liar_count} 人 | 诚实者：{config.honest_count} 人
- 问答轮数：{config.rounds} 轮
- 回响系统：{'开启' if config.enable_echo else '关闭'}
"""
    console.print(Markdown(md))


def show_participants(agents, reveal_roles: bool = False):
    """展示参与者列表"""
    table = Table(title="参与者")
    table.add_column("姓名", style="cyan")
    table.add_column("年龄", style="dim")
    table.add_column("背景", style="green")
    table.add_column("回响", style="magenta")
    if reveal_roles:
        table.add_column("身份", style="red")

    for a in agents:
        p = a.player.personality
        echo_name = p.echo.name if p.echo else "无"
        row = [p.name, str(p.age), p.background[:40], echo_name]
        if reveal_roles:
            row.append(a.player.role.value)
        table.add_row(*row)

    console.print(table)


def show_host_intro(host_name: str, announcement: str):
    """生肖主持人开场"""
    console.print(Rule(f"[red]{host_name}"))
    console.print(Panel(Markdown(announcement), border_style="red"))


def show_round_header(round_num: int, total: int):
    """轮次标题"""
    console.print()
    console.print(Rule(f"[yellow]第 {round_num}/{total} 轮 — 问答"))


def show_question(round_num: int, asker: str, target: str, question: str):
    """提问"""
    md = f"### 🔍 {asker} → {target}\n\n> {question}"
    console.print(Panel(Markdown(md), border_style="blue"))
    _log("question", {"round": round_num, "from": asker, "to": target, "content": question})


def show_answer(respondent: str, answer: str, role: Role):
    """回答"""
    icon = "🔴" if role == Role.LIAR else "🟢"
    md = f"### {icon} {respondent} 回答\n\n{answer}"
    console.print(Panel(Markdown(md), border_style="green"))
    _log("answer", {"from": respondent, "content": answer})


def show_thinking(name: str, thinking: str):
    """内部思考（调试）"""
    console.print(Text(f"💭 {name}: {thinking}", style="dim italic"))


def show_host_comment(host: str, comment: str):
    """生肖评论"""
    console.print(Text(f"🐑 {host}: {comment}", style="red italic"))


def show_vote_header():
    """投票阶段"""
    console.print()
    console.print(Rule("[bold red]投票阶段"))


def show_vote(voter: str, target: str, reason: str):
    """单次投票"""
    console.print(Markdown(f"**{voter}** → **{target}**：{reason}"))
    _log("vote", {"voter": voter, "target": target, "reason": reason})


def show_result(result: GameResult):
    """游戏结果"""
    console.print()
    winner_style = "green" if result.winner == Role.HONEST else "red"
    console.print(Rule(f"[bold {winner_style}]游戏结果"))

    winner_text = "🎉 诚实者获胜！" if result.winner == Role.HONEST else "💀 说谎者获胜！"
    console.print(Markdown(f"## {winner_text}"))
    console.print(Markdown(f"> {result.summary}"))

    # 投票统计
    table = Table(title="投票统计")
    table.add_column("被投者", style="cyan")
    table.add_column("票数", style="yellow")
    for name, count in sorted(result.vote_tally.items(), key=lambda x: x[1], reverse=True):
        table.add_row(name, str(count))
    console.print(table)

    # 回响觉醒
    if result.awakening_results:
        console.print(Markdown("### 回响觉醒"))
        for r in result.awakening_results:
            if r.awakened:
                console.print(Markdown(f"- **{r.character_name}** 觉醒了回响「{r.echo_name}」— {r.trigger_event}"))


def show_cycle_end(cycle: int):
    """终焉之日"""
    console.print()
    console.print(Rule("[bold]终焉之日"))
    console.print(Markdown(f"第 **{cycle}** 轮回结束。记忆消散……唯有觉醒者保留片段。"))


# ═══════════════════════════════════════════════════
# JSON 日志
# ═══════════════════════════════════════════════════

def _log(event_type: str, data: dict):
    data["type"] = event_type
    data["timestamp"] = datetime.now().isoformat()
    _json_buffer.append(data)


def clear_log():
    _json_buffer.clear()


def save_json_log(filepath: str, extra: Optional[dict] = None) -> str:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    log = {
        "game": "说谎者",
        "events": list(_json_buffer),
        **(extra or {}),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    console.print(Markdown(f"📄 完整日志已保存至：`{path}`"))
    return str(path)

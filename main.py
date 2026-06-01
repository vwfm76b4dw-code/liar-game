"""入口 — 说谎者 AI Agent 游戏

用法:
    python main.py                    # 默认9人局
    python main.py --players 7        # 7人局
    python main.py --rounds 4         # 4轮问答
    python main.py --reveal           # 公开思考过程
    python main.py --cycles 3         # 运行3个轮回
    python main.py --host 人鼠        # 指定生肖主持人
"""

from __future__ import annotations
import argparse
import sys
import os

# 强制 UTF-8 输出（解决 Windows 终端乱码）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from config import GameConfig, LLMConfig
from display import console, clear_log, save_json_log
from game_engine import GameEngine
from llm_client import LLMClient
from models import Role
from rich.markdown import Markdown


def parse_args():
    p = argparse.ArgumentParser(description="说谎者 — 来自《十日终焉》的AI Agent游戏")
    p.add_argument("--players", type=int, default=9, help="总参与者数（默认9）")
    p.add_argument("--liars", type=int, default=None, help="说谎者数量（默认1）")
    p.add_argument("--rounds", type=int, default=3, help="问答轮数（默认3）")
    p.add_argument("--cycles", type=int, default=1, help="轮回次数（默认1）")
    p.add_argument("--host", type=str, default="人羊", help="生肖主持人（默认人羊）")
    p.add_argument("--model", type=str, default="deepseek-chat", help="DeepSeek模型")
    p.add_argument("--temperature", type=float, default=0.7, help="LLM温度")
    p.add_argument("--reveal", action="store_true", help="公开Agent思考过程")
    p.add_argument("--output", type=str, default="logs/game.json", help="JSON日志路径")
    p.add_argument("--dry-run", action="store_true", help="仅预览配置")
    return p.parse_args()


def main():
    args = parse_args()

    if not args.dry_run and not LLMConfig.validate():
        console.print(Markdown("""
## 未配置 DeepSeek API Key

请设置环境变量：
```bash
export DEEPSEEK_API_KEY="sk-your-key-here"
```

或在项目根目录创建 `.env` 文件：
```
DEEPSEEK_API_KEY=sk-your-key-here
```
"""))
        sys.exit(1)

    game_config = GameConfig()
    game_config.total_players = args.players
    game_config.liar_count = args.liars or max(1, args.players // 9)
    game_config.rounds = args.rounds
    game_config.reveal_thinking = args.reveal
    game_config.host_name = args.host

    llm_config = LLMConfig()
    llm_config.model = args.model
    llm_config.temperature = args.temperature

    if game_config.liar_count >= game_config.total_players:
        console.print("[red]错误：说谎者数量不能 >= 总参与者数")
        sys.exit(1)

    if args.dry_run:
        console.print(Markdown(f"""
## 配置预览

| 参数 | 值 |
|------|-----|
| 总参与者 | {game_config.total_players} |
| 说谎者 | {game_config.liar_count} |
| 诚实者 | {game_config.honest_count} |
| 轮数 | {game_config.rounds} |
| 轮回 | {args.cycles} |
| 主持人 | {game_config.host_name} |
| 模型 | {llm_config.model} |
| 温度 | {llm_config.temperature} |
"""))
        return

    clear_log()
    llm = LLMClient(llm_config)
    engine = GameEngine(config=game_config, llm=llm)

    result = None
    try:
        if args.cycles > 1:
            results = engine.run_cycles(args.cycles)
            for i, r in enumerate(results):
                engine.save_log(r, f"logs/game_cycle_{i+1}.json")
            result = results[-1]
        else:
            result = engine.run_single_game()
            engine.save_log(result, args.output)

        sys.exit(0 if result.winner == Role.HONEST else 1)

    except KeyboardInterrupt:
        console.print("\n[red]游戏被中断")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]游戏出错：{e}")
        raise


if __name__ == "__main__":
    main()

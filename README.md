# 说谎者 — AI Agent 游戏

基于中国网络小说 **《十日终焉》** 的 AI Agent 推理游戏。使用 DeepSeek API 驱动的 LLM Agent，模拟终焉之地的「说谎者」生死游戏。

## 游戏背景

在终焉之地，被选中的参与者们被迫参加由**生肖主持人**掌控的生死游戏。本次游戏为「说谎者」—— N 名参与者中潜伏着少数**说谎者**，他们必须在每句话中撒谎。诚实者则需要通过提问和推理找出说谎者。投票阶段，被最多人怀疑的参与者将被淘汰。

## 游戏规则

| 要素 | 说明 |
|------|------|
| 参与者 | 默认 9 人（可自定义） |
| 说谎者 | 默认 1 人（可自定义） |
| 问答轮数 | 默认 3 轮 |
| 诚实者规则 | 每句话必须为真话 |
| 说谎者规则 | 每句话必须为假话 |
| 投票 | 每人投票选出最怀疑的对象 |
| 胜负 | 所有说谎者被找出 → 诚实者胜；有说谎者逃脱 → 说谎者胜 |

## 核心特性

- **AI Agent 角色扮演**：每个角色拥有独立的人格、背景和策略，由 LLM 驱动真实互动
- **回响系统**：忠于原作的「回响」觉醒机制 — 满足条件觉醒，保留跨轮回记忆
- **多轮回**：支持多次轮回，觉醒者保留记忆，未觉醒者记忆清零
- **生肖主持人**：4 位生肖主持人（人羊、人鼠、地蛇、天龙），各具特色
- **多组织**：天堂口、猫、极道三大势力的角色互动
- **双线输出**：终端 Rich 美化输出 + JSON 结构化日志

## 架构

```
liar-game/
├── main.py              # CLI 入口
├── server.py            # FastAPI 服务器
├── config.py            # 配置与角色加载
├── models.py            # Pydantic 数据模型
├── llm_client.py        # DeepSeek API 封装
├── agent.py             # 参与者 + 生肖 Agent
├── game_engine.py       # 游戏编排引擎
├── memory_manager.py    # 跨轮回记忆管理
├── echo_system.py       # 回响觉醒判定
├── display.py           # Rich 终端输出
├── games/
│   ├── __init__.py
│   ├── base.py          # 游戏基类
│   └── liar_game.py     # 说谎者游戏实现
├── prompts/
│   └── templates.py     # 系统提示词模板
├── data/
│   ├── characters.json  # 9 位《十日终焉》角色
│   ├── zodiacs.json     # 4 位生肖主持人
│   ├── organizations.json  # 3 大组织
│   └── memories/        # 角色记忆持久化
├── logs/                # 游戏日志输出
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 方式一：环境变量
export DEEPSEEK_API_KEY="sk-your-key-here"

# 方式二：.env 文件
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 3. 运行游戏

```bash
# 默认 9 人局
python main.py

# 7 人局，4 轮问答，公开思考过程
python main.py --players 7 --rounds 4 --reveal

# 运行 3 个轮回
python main.py --cycles 3

# 指定地蛇为主持人
python main.py --host 地蛇

# 预览配置
python main.py --dry-run
```

### 4. API 服务器

```bash
uvicorn server:app --reload
```

```bash
# 创建游戏
curl -X POST http://localhost:8000/game/start \
  -H "Content-Type: application/json" \
  -d '{"players": 9, "liars": 1, "rounds": 3}'

# 运行游戏
curl -X POST http://localhost:8000/game/run

# 查询角色记忆
curl http://localhost:8000/game/memories/齐夏
```

## 角色列表

| 角色 | 年龄 | 背景 | 回响 |
|------|------|------|------|
| 齐夏 | 26 | 谋略家，自称骗子 | 生生不息 |
| 乔家劲 | 28 | 前特种兵，忠诚卫士 | 破万法 |
| 陈俊南 | 30 | 情报贩子，猫组织首领 | 魂迁 |
| 章晨泽 | 32 | 刑警，理性推理者 | 激发 |
| 楚天秋 | 35 | 天堂口首领，野心家 | 无 |
| 林檎 | 24 | 外科医生，冷静精准 | 招灾 |
| 韩一墨 | 29 | 小说家，想象力丰富 | 巧物 |
| 甜甜 | 22 | 花店老板，温柔乐观 | 强运 |
| 余念安 | 25 | 作家，齐夏的青梅竹马 | 替罪 |

## 生肖主持人

| 名称 | 等级 | 面具 | 残忍度 |
|------|------|------|--------|
| 人羊 | 人级 | 羊 | 7/10 |
| 人鼠 | 人级 | 鼠 | 5/10 |
| 地蛇 | 地级 | 蛇 | 9/10 |
| 天龙 | 天级 | 龙 | 8/10 |

## 设计理念

1. **忠于原作**：尽可能还原《十日终焉》的世界观、角色性格和游戏机制
2. **AI 原生**：每个角色都是独立的 LLM Agent，拥有自己的记忆、怀疑度和策略
3. **可扩展**：通过基类继承可以添加新的游戏类型（是与非、雨后春笋等）
4. **可观测**：Rich 终端输出 + JSON 日志双格式，便于调试和分析

## 扩展点

- 添加新角色：编辑 `data/characters.json`
- 添加新游戏类型：继承 `games/base.py` 的 `BaseGame` 类
- 添加新提示词模板：编辑 `prompts/templates.py`
- 添加新回响：编辑 `echo_system.py` 的 `_echo_defs`
- 切换 LLM：修改 `llm_client.py`，兼容 OpenAI SDK

## 许可

本项目仅供学习和研究使用。角色和世界观版权归原著《十日终焉》所有。

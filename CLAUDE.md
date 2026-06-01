# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## 项目概述

说谎者 AI Agent 游戏，基于中国网络小说《十日终焉》世界观。使用 DeepSeek API 驱动多个 LLM Agent 进行角色扮演和推理博弈。

## 常用命令

```bash
# 运行游戏（默认9人局）
python main.py

# 预览配置
python main.py --dry-run

# 自定义参数运行
python main.py --players 7 --rounds 4 --reveal

# 多轮回运行
python main.py --cycles 3 --host 地蛇

# 启动 API 服务器
uvicorn server:app --reload --port 8000

# 安装依赖
pip install -r requirements.txt
```

## 架构概览

```
CLI (main.py) 或 API (server.py)
        │
        ▼
  GameEngine (game_engine.py)  ← 编排器
        │
        ├── config.py          ← 加载角色/生肖/配置
        ├── models.py          ← 所有 Pydantic 数据模型
        ├── llm_client.py      ← DeepSeek API 封装 (OpenAI SDK 兼容)
        │
        ├── ParticipantAgent   ← 参与者 Agent (agent.py)
        │   ├── prompts/       ← 系统提示词模板
        │   ├── memory_manager ← 跨轮回记忆
        │   └── echo_system    ← 回响觉醒判定
        │
        ├── ZodiacAgent        ← 生肖主持人 Agent (agent.py)
        │
        ├── LiarGame           ← 说谎者游戏逻辑 (games/liar_game.py)
        │   └── BaseGame       ← 游戏基类 (games/base.py)
        │
        └── display.py         ← Rich 终端输出 + JSON 日志
```

## 关键设计决策

### 1. Agent 独立性
每个 `ParticipantAgent` 拥有独立的系统提示词、记忆、怀疑度追踪和思考记录。Agent 之间不直接通信，所有交互通过 `GameEngine` 和 `LiarGame` 编排。

### 2. 角色分配
角色（Personality）和身份（Role: 诚实者/说谎者）在 `GameEngine.create_game()` 中**随机抽取并随机分配**，确保每局游戏的组合不同。

### 3. 提示词模板
系统提示词使用 Python `str.format()` 而非 Jinja2，便于在代码中动态替换。模板位于 `prompts/templates.py`。

### 4. 回响系统
回响觉醒基于关键词匹配（`echo_system.py`），而非 LLM 判断。这是出于确定性和成本的考量。觉醒者可以在下一轮回中保留记忆。

### 5. 记忆持久化
角色记忆以 JSON 文件形式存储在 `data/memories/{name}.json`，轮回结束时清理未觉醒者的记忆。

### 6. LLM 输出约束
所有 LLM 调用使用 JSON mode（`response_format: json_object`），并在 `parse_json()` 中进行容错解析（支持裸 JSON、markdown 代码块、部分提取）。

## 数据模型（models.py）

核心枚举和模型：
- `Role`: HONEST（诚实者）、LIAR（说谎者）、HOST（生肖）
- `ZodiacTier`: HEAVEN（天级）、EARTH（地级）、HUMAN（人级）
- `Player`: 参与者（Personality + Role）
- `ZodiacHost`: 生肖主持人（Personality + 面具 + 残酷度）
- `GameSession`: 一局游戏的完整状态
- `GameResult`: 游戏结果（胜者、投票统计、觉醒结果）

## 扩展点

### 添加新游戏类型
1. 在 `games/` 下新建文件，继承 `BaseGame`
2. 实现 `setup()`, `run_round()`, `run_voting()`, `determine_result()`, `run()`
3. 在 `models.py` 的 `GameType` 枚举中添加新类型
4. 在 `game_engine.py` 中添加对应的创建逻辑

### 添加新角色
编辑 `data/characters.json`，确保字段匹配 `Personality` 模型。

### 添加新回响
编辑 `echo_system.py` 的 `_echo_defs` 字典，添加名称、条件、触发描述和效果。

### 切换 LLM 提供商
修改 `llm_client.py`，当前使用 OpenAI SDK 兼容 DeepSeek API。修改 `base_url` 和 `api_key` 即可切换到其他兼容 OpenAI 接口的服务。

## 注意事项

- `.env` 文件包含 API Key，不可提交到版本控制
- `data/memories/` 目录中的文件是运行时生成的，也不应提交
- `logs/` 目录输出游戏日志，每次运行生成新文件
- 游戏配置通过 CLI 参数传入，不使用配置文件
- 所有中文文本使用 UTF-8 编码

<h1 align="center">🎭 说谎者 · 终焉之地</h1>
<h1 align="center">The Liar · Terminal Land</h1>

<p align="center">
  <strong>基于《十日终焉》的 AI 角色扮演博弈游戏</strong>
  <br>
  <strong>An AI Role-Playing Deception Game based on the novel "Ten Days to Eternity"</strong>
  <br><br>
  DeepSeek V4-Pro / V4-Flash · 9 Characters · Auto/Manual Modes · WeChat-style UI
</p>

<p align="center">
  <a href="https://github.com/vwfm76b4dw-code/liar-game">GitHub</a> ·
  <a href="#-关于十日终焉">📖 关于原著</a> ·
  <a href="#-changelog">📝 Changelog</a>
</p>

---

## 📖 关于《十日终焉》/ About the Novel

> *十日终焉（Ten Days to Eternity）* 是中国网络作家 **烟灰** 创作的悬疑推理小说，连载于起点中文网。
> 故事讲述一群被困在「终焉之地」的人们，被迫参加由十二生肖主持的死亡游戏。
> 每个游戏都是对人性的极致考验——说谎、信任、背叛、牺牲。
> 角色们在无尽的轮回中寻找真相、救赎与自由。

> *"Ten Days to Eternity" is a Chinese web novel by **Yan Hui**, serialized on Qidian.
> It tells the story of people trapped in the "Terminal Land", forced to participate in deadly games
> hosted by the Chinese Zodiac. Each game is an ultimate test of human nature — lying, trust, betrayal, sacrifice.
> Characters seek truth, redemption, and freedom through endless cycles.*

- **作者 / Author**: 烟灰 (Yan Hui)
- **平台 / Platform**: 起点中文网 (Qidian) · [查看原著]()
- **标签 / Tags**: 悬疑 · 推理 · 智斗 · 轮回 · 群像

---

## 🌍 世界观 / World Setting

> *「你们当中，**有且只有一个说谎者**。抽到说谎者的人，必须在故事中掺杂谎言。」*
> *——🐑 人羊*

> *"Among you, there is **only one liar**. The one who draws the liar card must weave lies into their story."*
> *—— 🐑 Goat*

**中文：**
在**终焉之地**，被选中的参与者们被迫参加由生肖主持人掌控的生死游戏。九个人围坐在一张斑驳的圆桌前，每人抽一张背写「女娲游戏」的卡牌——其中一张是「说谎者」。
规则看似简单——每人讲述自己的死亡故事，说谎者必须在故事中掺杂谎言。讨论、投票、处决。
但真相远不止于此：**所有人抽到的都是「说谎者」**，每人都在欺骗彼此，也都在被规则欺骗。

**English:**
In the **Terminal Land**, selected participants are forced to play life-or-death games hosted by the Zodiac. Nine people sit around a worn round table, each drawing a card with "Nuwa Game" on the back — one of them is the "Liar".
The rules seem simple — each person tells their death story, and the liar must weave lies into it. Discussion, voting, execution.
But the truth runs deeper: **everyone drew the "Liar" card**. Everyone is deceiving each other, and everyone is being deceived by the rules.

---

## ✨ 核心特性 / Features

### 🎮 双模式游玩 / Dual Game Modes
| 模式 / Mode | 说明 / Description |
|------------|-------------------|
| **👑 观察者模式 / Observer** | 以人羊视角旁观，AI 自动推进 / Watch as Goat, AI auto-plays |
| **🎮 角色接管 / Possess** | 点击角色切换视角，手动操控发言投票 / Click to possess any character |

### 🤖 AI 驱动 / AI-Powered
- **齐夏 → DeepSeek V4-Pro**（深度推理 16K 预算 / Deep reasoning, 16K thinking budget）
- **其余 8 人 → DeepSeek V4-Flash**（快速响应 / Fast response）
- 每位角色独立提示词、心理状态、背景档案 / Per-character system prompts & psychological profiles
- AI **思考过程**实时展示（仅操控者可见） / Real-time **thinking process** visible only to the controller
- **✨ AI 辅助 / AI Assist**：一键生成发言建议 / One-click suggestion generation

### 💬 微信风格聊天 / WeChat-style Chat
- SVG 像素风头像 / SVG pixel-art avatars
- 消息气泡按类型分色 / Color-coded message bubbles
- 左侧角色列表一键切换视角 / One-click perspective switch
- 智能自动滚动 / Smart auto-scroll

### 🧠 回响系统 / Echo System
忠于原著——当角色的**思考过程**流露觉醒契机时触发回响（基于 `agent.thoughts` 而非公开发言判定）：
Faithful to the novel — Echos are triggered when a character's **thought process** reveals awakening conditions (judged by `agent.thoughts`, not public speech):

| 角色 Character | 回响 Echo | 觉醒契机 Trigger |
|---------------|-----------|-----------------|
| 齐夏 | 灵闻 / Sound | 对妻子的执念 / Obsession with his wife |
| 乔家劲 | 破万法 / Breaker | 保护他人的信念 / Belief in protecting others |
| 甜甜 | 巧物 / Crafter | 帮助他人的渴望 / Urge to help |
| 赵海博 | 离析 / Dissolve | 洞察万物结构 / Perceiving structure |
| 韩一墨 | 招灾 / Disaster | 极致的恐惧 / Extreme fear |
| 章晨泽 | 移魂 / Soul Shift | 面对不公 / Facing injustice |
| 李尚武 | 探囊 / Reach | 保护他人的决意 / Determination to protect |
| 林檎 | 激发 / Inspire | 激励他人 / Inspiring others |
| 肖冉 | 祸水 / Plague | 依附强者 / Clinging to power |

### 🗳 投票机制 / Voting
- 全员投票给人羊 → 众人获胜 / Vote Goat unanimously → **Players win**
- 投票不统一 → 全员处决，人羊获胜 / Split vote → **Goat wins**, all executed
- 已接管角色可手动投票 / Possessed characters can vote manually

### 📜 对话导出 / Export
点击 💾 导出完整对话记录 `.txt` / Click 💾 to export full chat history as `.txt`

---

## 🏗️ 项目架构 / Architecture

```
liar-game/
├── web_app.py              # FastAPI 主服务器 / Main server
├── templates/
│   └── liar_web.html       # 前端 UI / Frontend
├── static/fonts/           # 字体 / Fonts
├── agent.py                # AI Agent（参与者+主持人 / Characters + Host）
├── llm_client.py           # DeepSeek API 封装 / API wrapper
├── config.py               # 配置 / Config
├── models.py               # 数据模型 / Data models
├── echo_system.py          # 回响觉醒 / Echo awakening
├── memory_manager.py       # 跨轮回记忆 / Cross-cycle memory
├── game_engine.py          # CLI 游戏引擎 / CLI engine
├── main.py                 # CLI 入口 / CLI entry
├── data/
│   ├── characters.json     # 角色档案 / Character profiles
│   ├── zodiacs.json        # 生肖主持人 / Zodiac hosts
│   └── organizations.json  # 组织 / Organizations
├── prompts/
│   └── templates.py        # 提示词模板 / Prompt templates
└── games/
    ├── base.py             # 游戏基类 / Base game
    └── liar_game.py        # 说谎者逻辑 / Liar game logic
```

---

## 🚀 快速开始 / Quick Start

### 1. 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key / Configure

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
# Edit .env and fill in your DeepSeek API Key
```

`.env`:
```env
DEEPSEEK_API_KEY="sk-your-key-here"
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
DEEPSEEK_THINKING_BUDGET=16384
```

### 3. 启动 Web 服务器 / Start Server

```bash
python web_app.py
```

Open **http://localhost:8910**

### 4. 游戏操作 / Game Controls

| 操作 Action | 方式 Control |
|------------|-------------|
| **开始游戏 Start** | 点击「进入游戏」/ Click "Enter Game" |
| **自动推进 Auto** | 点击顶部「▶ 自动」/ Click "▶ Auto" |
| **暂停/继续 Pause** | 点击「⏸」/ Click "⏸" |
| **切换视角 Switch** | 点击左侧角色 / Click character in sidebar |
| **接管角色 Possess** | 点击「🎮 接管」/ Click "🎮 Take Over" |
| **手动发言 Speak** | 输入文字按回车 / Type and press Enter |
| **AI 辅助 Assist** | 点击「✨ AI帮写」/ Click "✨ AI Assist" |
| **释放角色 Release** | 点击「释放」/ Click "Release" |
| **导出对话 Export** | 点击顶部「💾」/ Click top "💾" |
| **停止 Stop** | 点击「⏹」/ Click "⏹" |

---

## 🎭 角色档案 / Characters

### 🃏 齐夏 (Qi Xia) — 永恒的殉道者 / Eternal Martyr
> *「一切皆为棋子，包括我自己。」 / "Everything is a pawn, including me."*

26 岁，青岛人，职业骗子。曾化身「白羊」生肖被天龙暗算，因妻子假消息被撬棍击毙。
回响 Echo：**灵闻 / Sound Sense**

### 🤜 乔家劲 (Qiao Jiajin) — 市井赤子 / Street Knight
> *「滴水之恩，涌泉相报。」 / "A drop of kindness returns as a gushing spring."*

28 岁，香港砵兰街人。替恩人顶罪入狱 4 年，为兄弟复仇被推下天台。
回响 Echo：**破万法 / Breaker**

### 🍎 林檎 (Lin Qin) — 终焉之地的亲生女儿 / The Land's Own Daughter
> *「我的记忆是假的——那我还算活着吗？」 / "My memories are fake — am I even alive?"*

24 岁。实为终焉之地孕育的第一颗果实，被青龙化形为人类。
回响 Echo：**激发 / Inspire**

### 👧 甜甜 (Tiantian) — 坚韧的负重者 / Resilient Bearer
> *「我早就失去一切了，所以我不怕再失去什么。」 / "I've already lost everything, so I'm not afraid to lose anymore."*

22 岁，陕西农村女孩。为弟弟手术费辍学打工，被工厂孤立，千里背债。
回响 Echo：**巧物 / Crafter**

### 🛡️ 李尚武 (Li Shangwu) — 灰色执法者 / Gray Enforcer
> *「别怕，叔叔在这儿。」 / "Don't be afraid, Uncle is here."*

35 岁，内蒙刑侦支队长。为女儿治病沦为黑警，追捕毒贩中被击中牺牲。
回响 Echo：**探囊 / Reach**

### 👻 韩一墨 (Han Yimo) — 被恐惧围猎者 / Hunted by Fear
> *「越害怕的事情，就越会发生。」 / "The more you fear something, the more it happens."*

29 岁，广西网络作家。造黄谣害死无辜女生，保留七年轮回记忆。
回响 Echo：**招灾 / Disaster**

### 💣 肖冉 (Xiao Ran) — 扭曲的寄生者 / Twisted Parasite
> *「到死她都不知道，那个女孩是否就是被她拐走的。」 / "To her death, she never knew if that girl was one she trafficked."*

23 岁，大理幼师。贩卖儿童并栽赃同事，被车撞死。
回响 Echo：**祸水 / Plague**

### ⚖️ 章晨泽 (Zhang Chenze) — 破茧的复仇者 / Avenger Reborn
> *「法律给不了我公平——所以我亲手拿了。」 / "The law couldn't give me justice — so I took it myself."*

32 岁，四川律师。被父母卖给屠户，杀掉全家后地震中坠落。
回响 Echo：**移魂 / Soul Shift**

### 🔪 赵海博 (Zhao Haibo) — 破碎的救赎者 / Broken Redeemer
> *「只要我尽力了，就可以心安理得。」 / "As long as I did my best, I can be at peace."*

45 岁，江苏脑外科医生。地震中放弃逃生救患者，被天花板砸死。
回响 Echo：**离析 / Dissolve**

---

## 🐑 生肖主持人 / Zodiac Hosts

| 名称 Name | 等级 Tier | 面具 Mask | 残暴 Cruelty |
|-----------|----------|-----------|-------------|
| 人羊 Goat | 人级 Human | 🐑 | 7/10 |
| 人鼠 Rat | 人级 Human | 🐀 | 5/10 |
| 地蛇 Snake | 地级 Earth | 🐍 | 9/10 |
| 天龙 Dragon | 天级 Heaven | 🐉 | 8/10 |

---

## 🔧 开发扩展 / Development

- **添加角色 / Add Characters**: 编辑 `data/characters.json`
- **修改回响 / Modify Echos**: 编辑 `echo_system.py` 的 `ECHO_DEFS`
- **切换 LLM / Switch LLM**: 修改 `.env` 模型名 / Change model name in `.env`
- **自定义提示词 / Custom Prompts**: 编辑 `prompts/templates.py`
- **添加游戏类型 / Add Game Type**: 继承 `games/base.py`

---

## 📝 Changelog / 更新日志

> 仅记录当前版本更新。历史版本参见 git log。
> Only current version updates are listed. See git log for history.

### v1.0.0 — 2026-06-01

#### ✨ 新功能 / Features
- DeepSeek V4-Pro / V4-Flash 双模型驱动（齐夏 V4-Pro，其余 V4-Flash）
- 微信风格聊天 UI，SVG 像素风角色头像
- 视角切换系统（人羊观察者 / 角色第一人称）
- 角色手动接管 + 释放（输入即自动接管）
- AI 辅助发言建议一键生成
- 回响觉醒系统（基于思考过程 `agent.thoughts` 判定）
- 自动流程 + 暂停 / 继续 / 停止
- 投票阶段支持手动接管
- 对话导出为 .txt 文件
- 智能自动滚动（仅在底部时跟随）
- API 失败使用 `[待补充]` 占位符，避免伪人话

#### 🎭 角色 / Characters
- 9 位面试房间角色完整原著档案
- 每位角色独立系统提示词、心理状态、死亡故事
- 跨轮回记忆系统

#### 🔧 技术 / Tech
- FastAPI + 异步自动流程
- ThreadPoolExecutor 隔离阻塞 LLM 调用
- 前端轮询状态同步（1.2s 间隔）
- 乐观 UI 更新（视角切换即时响应）

---

## 📜 许可 / License

本项目仅供学习和研究使用。《十日终焉》角色和世界观版权归作者 **烟灰** 所有。
This project is for learning and research purposes only. "Ten Days to Eternity" characters and world are copyrighted by author **Yan Hui**.

"""轮回记忆管理器 -- 文件级持久化

每个角色在 data/memories/{name}.json 中保存跨轮回记忆。
觉醒回响的角色可在下一轮回保留部分记忆。
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional

from models import CycleMemory


class MemoryManager:
    """文件级轮回记忆管理器"""

    def __init__(self, memories_dir: Optional[Path] = None):
        from config import MEMORIES
        self.dir = Path(memories_dir) if memories_dir else MEMORIES
        os.makedirs(self.dir, exist_ok=True)

    def _path(self, name: str) -> Path:
        safe = name.replace(" ", "_").replace("/", "_")
        return self.dir / f"{safe}.json"

    def load(self, name: str) -> dict:
        p = self._path(name)
        if not p.exists():
            return {
                "character_name": name,
                "awakened": False,
                "memory_across_cycles": [],
            }
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, name: str, data: dict):
        with open(self._path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_cycle_memories(self, name: str, cycle_id: int) -> list[CycleMemory]:
        data = self.load(name)
        memories = []
        for m in data.get("memory_across_cycles", []):
            if m.get("cycle_id") == cycle_id:
                memories.append(CycleMemory(**m))
        return memories

    def add_memory(self, name: str, memory: CycleMemory):
        data = self.load(name)
        data.setdefault("memory_across_cycles", []).append(memory.model_dump())
        data["awakened"] = True
        self.save(name, data)

    def is_awakened(self, name: str) -> bool:
        return self.load(name).get("awakened", False)

    def get_all_memories(self, name: str) -> list[dict]:
        return self.load(name).get("memory_across_cycles", [])

    def wipe_non_awakened(self, names: list[str]):
        for name in names:
            data = self.load(name)
            if not data.get("awakened", False):
                self.save(name, {
                    "character_name": name,
                    "awakened": False,
                    "memory_across_cycles": [],
                })

    def format_for_prompt(self, name: str, max_memories: int = 5) -> str:
        memories = self.get_all_memories(name)
        if not memories:
            return "（无跨轮回记忆 -- 你未觉醒回响）"
        recent = sorted(
            memories,
            key=lambda m: m.get("importance", 1),
            reverse=True,
        )[:max_memories]
        lines = ["## 你的跨轮回记忆（回响觉醒）"]
        for m in recent:
            emo = m.get("emotion", "")
            desc = m.get("description", "")
            cid = m.get("cycle_id", "?")
            lines.append(f"- [第{cid}轮回] {desc} ({emo})")
        return "\n".join(lines)

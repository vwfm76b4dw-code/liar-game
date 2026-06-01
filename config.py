"""游戏配置与角色加载器"""
from __future__ import annotations
import json, os, random
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from models import Personality, ZodiacHost, ZodiacTier, EchoDef

load_dotenv()
ROOT = Path(__file__).parent
DATA = ROOT / 'data'
MEMORIES = DATA / 'memories'

class LLMConfig:
    api_key: str = os.getenv('DEEPSEEK_API_KEY', '')
    base_url: str = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model: str = os.getenv('DEEPSEEK_MODEL', 'deepseek-v4-pro')
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    @classmethod
    def validate(cls) -> bool:
        return bool(cls.api_key and cls.api_key != 'your_api_key_here')

class GameConfig:
    def __init__(self):
        self.total_players: int = 9
        self.liar_count: int = 1
        self.rounds: int = 3
        self.votes_per_player: int = 1
        self.enable_echo: bool = True
        self.enable_memory: bool = True
        self.reveal_thinking: bool = False
        self.game_type: str = '说谎者'
        self.host_name: str = '人羊'
    @property
    def honest_count(self) -> int:
        return self.total_players - self.liar_count

def load_characters(path: Optional[Path] = None) -> list[Personality]:
    path = path or DATA / 'characters.json'
    if not path.exists():
        raise FileNotFoundError(f'角色数据不存在: {path}')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Personality(**c) for c in data]

def load_zodiacs(path: Optional[Path] = None) -> list[ZodiacHost]:
    path = path or DATA / 'zodiacs.json'
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    results = []
    for z in data:
        pers = Personality(**z.pop('personality'))
        results.append(ZodiacHost(personality=pers, **z))
    return results

def pick_zodiac(name: str) -> Optional[ZodiacHost]:
    zodiacs = load_zodiacs()
    for z in zodiacs:
        if z.name == name:
            return z
    return None

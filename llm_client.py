"""DeepSeek API 客户端 — 兼容 OpenAI SDK

支持：
- 标准对话 (chat)
- JSON 模式 (json_mode)
- 自动重试 (exponential backoff)
- 容错 JSON 解析
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Optional, Any

from openai import OpenAI

from config import LLMConfig


class LLMClient:
    """DeepSeek API 客户端"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client: Optional[OpenAI] = None
        self.call_count = 0

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.config.api_key:
                raise RuntimeError("DEEPSEEK_API_KEY 未设置")
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._client

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """发送对话请求"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        # DeepSeek 最大思考强度（通过 extra_body 传递）
        if "deepseek" in self.config.model:
            kwargs["extra_body"] = {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": int(os.getenv("DEEPSEEK_THINKING_BUDGET", "8192")),
                }
            }

        if json_mode:
            if "deepseek" in self.config.model:
                kwargs["response_format"] = {"type": "json_object"}
            else:
                kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(3):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                self.call_count += 1
                return resp.choices[0].message.content or ""
            except Exception as e:
                last_error = e
                if attempt < 2:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"DeepSeek API 调用失败（重试3次）: {last_error}")

    def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: Optional[float] = None,
    ) -> dict:
        """发送对话请求，返回解析后的 JSON"""
        raw = self.chat(
            system_prompt, user_message,
            temperature=temperature, json_mode=True,
        )
        return parse_json(raw)


def parse_json(raw: str) -> dict:
    """容错 JSON 解析"""
    # 直接解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 提取 ```json ... ``` 块
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 找到第一个 { 和最后一个 }
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return {"raw_response": raw, "parse_error": True}

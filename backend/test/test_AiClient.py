"""
测试 AIClient 的三个方法。

运行方式（在 backend 目录下）：
    python -m pytest test/test_AiClient.py -v -s

或直接运行：
    python test/test_AiClient.py
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.core.config import Settings, get_settings
from app.modules.ai.client import AIClient


class FallbackOnlyAIClient(AIClient):
    """测试专用：跳过 primary，只走 fallback provider。"""

    def __init__(self, settings: Settings | None = None):
        super().__init__()
        if settings is not None:
            self.settings = settings

    async def chat_with_usage(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        provider = self.settings.ai_fallback
        if provider is None:
            raise RuntimeError(
                "fallback LLM 未配置。请检查 .env 中 "
                "AI_FALLBACK_ENABLED、AI_FALLBACK_API_KEY、AI_FALLBACK_BASE_URL、AI_FALLBACK_MODEL"
            )

        print(
            f"\n[TEST] 使用 fallback provider={provider.provider}, "
            f"model={provider.model}, base_url={provider.base_url}"
        )

        return await self._call_provider(
            provider=provider,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
        )


@pytest.fixture
def fallback_client(fallback_settings) -> FallbackOnlyAIClient:
    return FallbackOnlyAIClient(settings=fallback_settings)


@pytest.mark.asyncio
async def test_fallback_chat(fallback_client: FallbackOnlyAIClient):
    text = await fallback_client.chat(
        [
            {"role": "user", "content": "用一句话介绍 JobPilot 是什么"},
        ],
        max_tokens=128,
    )

    print("[chat result]", text)
    assert isinstance(text, str)
    assert len(text.strip()) > 0


@pytest.mark.asyncio
async def test_fallback_chat_with_usage(fallback_client: FallbackOnlyAIClient):
    result = await fallback_client.chat_with_usage(
        [
            {"role": "user", "content": "请回复：fallback LLM 测试成功"},
        ],
        max_tokens=128,
    )

    print("[chat_with_usage content]", result.content)
    print("[chat_with_usage usage]", result.usage.model_dump())

    assert result.provider  # 应为 qwen
    assert result.model
    assert isinstance(result.content, str)
    assert len(result.content.strip()) > 0
    assert result.usage.total_tokens >= 0


@pytest.mark.asyncio
async def test_fallback_chat_json(fallback_client: FallbackOnlyAIClient):
    data = await fallback_client.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "你只能返回 JSON，不要输出 markdown。"
                    '格式必须是 {"ok": true, "message": "..."}'
                ),
            },
            {"role": "user", "content": "返回一个测试成功响应"},
        ],
        max_tokens=256,
    )

    print("[chat_json result]", json.dumps(data, ensure_ascii=False, indent=2))

    assert isinstance(data, dict)
    assert "ok" in data


async def _run_manual() -> None:
    """不安装 pytest 时，可直接 python test/test_ai_client_fallback.py 运行。"""
    settings = get_settings()
    client = FallbackOnlyAIClient(settings=settings)

    print("=== 1. chat ===")
    text = await client.chat(
        [{"role": "user", "content": "用一句话介绍 JobPilot"}],
        max_tokens=128,
    )
    print(text)

    print("\n=== 2. chat_with_usage ===")
    result = await client.chat_with_usage(
        [{"role": "user", "content": "回复：fallback 测试成功"}],
        max_tokens=128,
    )
    print("content:", result.content)
    print("usage:", result.usage.model_dump())

    print("\n=== 3. chat_json ===")
    data = await client.chat_json(
        [
            {
                "role": "system",
                "content": '只返回 JSON：{"ok": true, "message": "..."}',
            },
            {"role": "user", "content": "返回测试 JSON"},
        ],
        max_tokens=256,
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_run_manual())
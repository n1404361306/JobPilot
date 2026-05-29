"""
AI Client 封装LLM API调用
提供 async chat、async chat_json、async chat_with_usage 方法。
"""
import json
import time
from typing import Any
# import asyncio

from openai import APIConnectionError, AsyncOpenAI, RateLimitError
from openai import APIStatusError, APITimeoutError

from app.core.exceptions import BusinessException
from app.core.config import LLMProviderSettings, Settings, get_settings
from app.modules.ai.schemas import AIChatResult, AIUsage

# 使用OpenAI SDK实现AI客户端

class RetryableAIError(Exception):
    """可重试的AI错误"""

class AIClient:
    def __init__(self):
        self.settings = get_settings()

    # 调用LLM API，返回文本
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        result = await self.chat_with_usage(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result.content
    

        # 调用LLM API，返回JSON格式文本
    async def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        json_schema: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        # json_schema 目前主要通过 system prompt 约束；此处预留参数
        _ = json_schema
        result = await self.chat_with_usage(
            messages,
            response_format={"type": "json_object"},
            temperature=0.1 if temperature is None else temperature,
            max_tokens=max_tokens,
        )
        try:
            return json.loads(result.content)
        except json.JSONDecodeError as exc:
            raise BusinessException(
                code=5002,
                message=f"LLM returned invalid JSON: {exc}",
            ) from exc
    
    async def chat_with_usage(
        self, 
        messages: list[dict[str,str]],
        *,
        response_format: dict[str,str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
        ) -> AIChatResult:
        # 调用LLM API，返回文本和使用情况
        providers : list[LLMProviderSettings] = [self.settings.ai_primary]
        fallback = self.settings.ai_fallback
        if fallback is not None:
            providers.append(fallback)
        
        last_error: Exception | None = None
        for provider in providers:
            try:
                return await self._call_provider(
                    provider=provider,
                    messages=messages,
                    response_format=response_format,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except RetryableAIError as exc:
                last_error = exc
                continue
        raise BusinessException(
            code=5001,
            message=f"all LLM providers failed: {last_error}",
        )

    async def _call_provider(
        self,
        *,
        provider: LLMProviderSettings,
        messages: list[dict[str,str]],
        response_format: dict[str,str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
        ) -> AIChatResult:
        if not provider.api_key:
            raise RetryableAIError("API key is empty")
        if not provider.base_url or not provider.model:
            raise RetryableAIError("Base URL or model is empty")

        client = AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
            timeout=self.settings.ai_timeout_seconds
        )
    
        request_kwargs: dict[str, Any] = {
            "model": provider.model,
            "messages": messages,
            "temperature": self.settings.ai_temperature if temperature is None else temperature,
            "max_tokens": self.settings.ai_max_tokens if max_tokens is None else max_tokens,
        }
        if response_format is not None:
            request_kwargs["response_format"] = response_format
        
        started = time.perf_counter()
        try:
            response = await client.chat.completions.create(**request_kwargs)
        except (APIConnectionError, RateLimitError, APITimeoutError) as exc:
            raise RetryableAIError(str(exc)) from exc
        except APIStatusError as exc:
            if exc.status_code in {429, 500, 502, 503, 504}:
                raise RetryableAIError(str(exc)) from exc
            raise BusinessException(
                code=5003,
                message = f"{provider.provider} request failed:{exc}") from exc
        finally:
            await client.close()
        
        
        duration_ms = int((time.perf_counter() - started) * 1000)

        content = response.choices[0].message.content or ""
        usage_raw = response.usage

        usage = AIUsage(
            provider=provider.provider,
            model=provider.model,
            input_tokens=getattr(usage_raw, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage_raw, "completion_tokens", 0) or 0,
            total_tokens=getattr(usage_raw, "total_tokens", 0) or 0,
            duration_ms=duration_ms,
        )
        return AIChatResult(
            content=content,
            usage=usage,
            provider=provider.provider,
            model=provider.model,
        )
                

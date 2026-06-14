import pytest

from app.modules.ai.client import AIClient
from app.modules.ai.prompt_constants import (
    AI_LOG_STATUS_FAILED,
    AI_LOG_STATUS_SUCCESS,
    PROMPT_TYPE_RESUME_GENERATE,
)
from app.modules.ai.log_service import AILogService, run_ai_with_log
from app.models.system_log import AICallLog

from app.core.config import Settings


def test_log_success(db):
    service = AILogService(db)
    record = service.log_success(
        user_id=1,
        model_name="qwen-test",
        prompt_type=PROMPT_TYPE_RESUME_GENERATE,
        input_tokens=100,
        output_tokens=200,
        duration_ms=1500,
    )

    assert record.id is not None
    assert record.status == AI_LOG_STATUS_SUCCESS
    assert record.user_id == 1
    assert record.prompt_type == PROMPT_TYPE_RESUME_GENERATE
    assert record.error_message is None


def test_log_failure(db):
    service = AILogService(db)
    record = service.log_failure(
        user_id=2,
        model_name="qwen-test",
        prompt_type=PROMPT_TYPE_RESUME_GENERATE,
        error_message="provider timeout",
        duration_ms=3000,
    )

    assert record.status == AI_LOG_STATUS_FAILED
    assert record.error_message == "provider timeout"
    assert record.input_tokens == 0


class SingleProviderAIClient(AIClient):
    """测试专用：强制只走指定的 primary 或 fallback provider。"""
    def __init__(self, settings: Settings, provider_name: str):
        super().__init__()
        self.settings = settings
        self.provider_name = provider_name
    async def chat_with_usage(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        if self.provider_name == "primary":
            provider = self.settings.ai_primary
        elif self.provider_name == "fallback":
            provider = self.settings.ai_fallback
            if provider is None:
                raise RuntimeError("fallback provider 未配置")
        else:
            raise ValueError(f"unknown provider_name: {self.provider_name}")
        print(
            f"\n[TEST] provider={provider.provider}, "
            f"model={provider.model}, base_url={provider.base_url}"
        )
        return await self._call_provider(
            provider=provider,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
        )
@pytest.mark.parametrize(
    "provider_name,user_id",
    [
        ("primary", 991),
        ("fallback", 992),
    ],
)

@pytest.mark.asyncio
async def test_run_ai_with_log_writes_record(db, llm_settings, provider_name, user_id):
    provider = (
        llm_settings.ai_primary
        if provider_name == "primary"
        else llm_settings.ai_fallback
    )
    assert provider is not None
    client = SingleProviderAIClient(llm_settings, provider_name)
    before_count = db.query(AICallLog).count()
    result = await run_ai_with_log(
        db,
        user_id=user_id,
        prompt_type=PROMPT_TYPE_RESUME_GENERATE,
        ai_client=client,
        model_name=provider.model,
        messages=[
            {
                "role": "user",
                "content": f"回复：{provider_name} provider 日志测试成功",
            }
        ],
        max_tokens=64,
    )
    after_count = db.query(AICallLog).count()
    assert after_count == before_count + 1
    assert isinstance(result.content, str)
    assert len(result.content.strip()) > 0
    latest = (
        db.query(AICallLog)
        .filter(AICallLog.user_id == user_id)
        .order_by(AICallLog.id.desc())
        .first()
    )
    assert latest is not None
    assert latest.prompt_type == PROMPT_TYPE_RESUME_GENERATE
    assert latest.status == AI_LOG_STATUS_SUCCESS
    assert latest.model_name == provider.model
    assert latest.input_tokens >= 0
    assert latest.output_tokens >= 0
    assert latest.duration_ms >= 0
   
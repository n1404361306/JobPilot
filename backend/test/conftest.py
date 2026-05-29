import pytest

from app.core.config import get_settings


@pytest.fixture(scope="session")
def fallback_settings():
    settings = get_settings()
    provider = settings.ai_fallback
    if provider is None:
        pytest.skip(
            "fallback LLM 未启用或未配置，请检查 .env 中的配置信息"
        )
    if not provider.api_key:
        pytest.skip("AI_FALLBACK_KEY 为空")
    if not provider.base_url or not provider.model:
        pytest.skip("AI_FALLBACK_BASE_URL 或 AI_FALLBACK_MODEL 为空")
    return settings
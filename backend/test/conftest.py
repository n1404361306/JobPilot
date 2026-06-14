import pytest

from app.core.config import get_settings

from app.db.session import SessionLocal
from sqlalchemy.orm import Session


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

@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try: 
        yield session
    finally:
        session.close()
    
@pytest.fixture(scope="session")
def llm_settings():
    """要求 primary 和 fallback 都已配置，供双 provider 集成测试使用。"""
    settings = get_settings()

    primary = settings.ai_primary
    if not primary.api_key or not primary.base_url or not primary.model:
        pytest.skip("primary LLM 未配置，请检查 AI_PRIMARY_KEY / BASE_URL / MODEL")

    fallback = settings.ai_fallback
    if fallback is None or not fallback.api_key or not fallback.base_url or not fallback.model:
        pytest.skip("fallback LLM 未配置，请检查 AI_FALLBACK_* 相关配置")

    return settings

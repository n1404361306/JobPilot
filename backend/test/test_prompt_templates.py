import pytest

from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_GENERATE
from app.modules.ai.prompt_service import PromptService


SAMPLE_VARIABLES = {
    "user_description": (
        "双非本科生，计算机科学与技术专业，熟悉 Python、FastAPI、MySQL。"
        "在 XX 公司实习一年，参与医疗管理系统后端开发。"
    ),
    "target_position": "Python 后端开发工程师",
    "resume_style": "简洁专业",
}


def test_resume_generate_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_RESUME_GENERATE, SAMPLE_VARIABLES)
    print(content)
    
    assert "Python 后端开发工程师" in content
    assert "education_list" in content
    assert "禁止编造" in content or "不得编造" in content
    assert "只返回 JSON" in content or "只返回JSON" in content


@pytest.mark.asyncio
async def test_resume_generate_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient

    service = PromptService(db)
    messages = service.build_messages(PROMPT_TYPE_RESUME_GENERATE, SAMPLE_VARIABLES)

    client = AIClient()
    data = await client.chat_json(messages, max_tokens=2048)

    assert isinstance(data, dict)
    assert "summary" in data
    assert "education_list" in data
    assert "project_list" in data
    assert "skill_list" in data
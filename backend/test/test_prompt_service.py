"""
PromptService单元测试
"""

import pytest

from app.modules.ai.prompt_service import PromptService
from app.modules.ai.client import AIClient

@pytest.mark.asyncio
async def test_prompt_service_with_ai_client(db, fallback_settings):
    _ = fallback_settings

    prompt_service = PromptService(db)
    ai_client = AIClient()

    messages = prompt_service.build_messages(
        "test_template",
        {
            "user_description": "双非本科生，计算机科学与技术专业，熟悉Python、FastAPI、MySQL。在XX公司进行过为期一年的实习，作为开发人员参与了医疗管理系统的后端开发，主要服务路由设计与服务层开发，涉及的技术为Python、MySQL、Git等",
            "target_position": "Python后端开发工程师",
        },
    )

    data = await ai_client.chat_json(
        messages,
        max_tokens = 1024
    )

    print(data)
    assert isinstance(data, dict)
    


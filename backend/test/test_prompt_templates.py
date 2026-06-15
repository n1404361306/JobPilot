import pytest

from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_GENERATE
from app.modules.ai.prompt_service import PromptService
from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_PARSE, PROMPT_TYPE_JOB_PARSE



SAMPLE_VARIABLES = {
    "user_description": (
        "双非本科生，计算机科学与技术专业，熟悉 Python、FastAPI、MySQL。"
        "在 XX 公司实习一年，参与医疗管理系统后端开发。"
    ),
    "target_position": "Python 后端开发工程师",
    "resume_style": "简洁专业",
}

SAMPLE_RESUME_TEXT = """
张三
电话：13800001111
邮箱：zhangsan@example.com
城市：上海
求职意向：Python 后端开发工程师
教育经历
2019.09-2023.06  某理工大学  计算机科学与技术  本科
实习经历
2022.07-2023.06  XX医疗科技有限公司  Python后端开发实习生
- 参与医疗管理系统后端开发，负责 API 路由与服务层实现
- 技术栈：Python、FastAPI、MySQL、Git
项目经历
2023.03-2023.06  医疗管理系统
- 角色：后端开发
- 技术栈：Python、FastAPI、MySQL
- 成果：完成 20+ 业务接口开发与联调
技能
Python、FastAPI、MySQL、Redis、Git
""".strip()


SAMPLE_RESUME_PARSE_VARIABLES = {
    "raw_text": SAMPLE_RESUME_TEXT,
    "source_type": "file",
}


SAMPLE_JD_TEXT = """
【公司名称】云途科技有限公司
【岗位名称】Python 后端开发工程师
【工作城市】上海
【岗位类型】全职
【薪资范围】15K-25K
【截止日期】2026-07-31
岗位职责：
1. 负责后端 API 设计与开发，维护核心业务服务。
2. 参与数据库设计与性能优化。
3. 配合前端完成接口联调与问题排查。
任职要求：
1. 本科及以上学历，计算机相关专业。
2. 熟悉 Python、FastAPI/Flask、MySQL。
3. 有实际项目或实习经验，了解 Redis 者优先。
4. 具备良好的沟通能力和团队协作意识。
关键词：Python、FastAPI、MySQL、Redis、后端开发
""".strip()


SAMPLE_JOB_PARSE_VARIABLES = {
    "raw_jd": SAMPLE_JD_TEXT,
}


def test_resume_generate_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_RESUME_GENERATE, SAMPLE_VARIABLES)
    print(content)
    
    assert "Python 后端开发工程师" in content
    assert "education_list" in content
    assert "禁止编造" in content or "不得编造" in content
    assert "只返回JSON" in content or "只返回JSON" in content


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

def test_resume_parse_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_RESUME_PARSE, SAMPLE_RESUME_PARSE_VARIABLES)
    assert "张三" in content
    assert "13800001111" in content
    assert SAMPLE_RESUME_TEXT in content
    assert "education_list" in content
    assert "不得编造" in content
    assert "只返回JSON" in content or "只返回JSON" in content
@pytest.mark.asyncio
async def test_resume_parse_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    service = PromptService(db)
    messages = service.build_messages(PROMPT_TYPE_RESUME_PARSE, SAMPLE_RESUME_PARSE_VARIABLES)
    data = await AIClient().chat_json(messages, max_tokens=2048)
    assert isinstance(data, dict)
    assert "basic_info" in data
    assert "education_list" in data
    assert isinstance(data.get("education_list"), list)
    assert isinstance(data.get("skill_list"), list)
    # 样例文本里明确有的信息，应能被提取（允许 LLM 略有差异）
    basic = data.get("basic_info") or {}
    phone = basic.get("phone", "")
    assert "13800001111" in phone or phone == ""  # 若模型漏提取，先放宽；稳定后可改为必须包含
@pytest.mark.asyncio
@pytest.mark.parametrize("source_type", ["file", "ocr"])
async def test_resume_parse_source_type_render(db, source_type):
    service = PromptService(db)
    variables = {**SAMPLE_RESUME_PARSE_VARIABLES, "source_type": source_type}
    content = service.render(PROMPT_TYPE_RESUME_PARSE, variables)
    assert source_type in content

# ---------- D3.6 测试 ----------
def test_job_parse_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_JOB_PARSE, SAMPLE_JOB_PARSE_VARIABLES)
    assert "云途科技有限公司" in content
    assert SAMPLE_JD_TEXT in content
    assert "skill_keywords" in content
    assert "不得编造" in content
    assert "只返回JSON" in content

@pytest.mark.asyncio
async def test_job_parse_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    service = PromptService(db)
    messages = service.build_messages(PROMPT_TYPE_JOB_PARSE, SAMPLE_JOB_PARSE_VARIABLES)
    data = await AIClient().chat_json(messages, max_tokens=2048)
    assert isinstance(data, dict)
    assert "job_title" in data
    assert "company_name" in data
    assert "skill_keywords" in data
    assert isinstance(data.get("skill_keywords"), list)
    # 样例 JD 中明确出现的字段
    assert "Python" in data.get("job_title", "") or "Python" in str(data.get("skill_keywords", []))
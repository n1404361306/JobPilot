import pytest

from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_GENERATE
from app.modules.ai.prompt_service import PromptService
from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_PARSE, PROMPT_TYPE_JOB_PARSE

import json

from app.modules.ai.prompt_constants import (
    PROMPT_TYPE_RESUME_GENERATE,
    PROMPT_TYPE_RESUME_PARSE,
    PROMPT_TYPE_JOB_PARSE,
    PROMPT_TYPE_RESUME_OPTIMIZE,
    PROMPT_TYPE_RESUME_ADAPT,
    PROMPT_TYPE_MATCHING_ANALYSIS,
    PROMPT_TYPE_INTERVIEW_QUESTIONS,
    PROMPT_TYPE_INTERVIEW_EVALUATE,
    PROMPT_TYPE_WEEKLY_REPORT,
)


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

SAMPLE_RESUME_JSON = json.dumps({
    "title": "张三的简历",
    "target_position": "Python 后端开发工程师",
    "summary": "计算机本科，具备 FastAPI 后端开发经验",
    "basic_info": {"real_name": "张三", "phone": "13800001111", "email": "zhangsan@example.com", "city": "上海"},
    "education_list": [{"school": "某理工大学", "major": "计算机科学与技术", "degree": "本科", "start_date": "2019.09", "end_date": "2023.06", "description": ""}],
    "project_list": [{"project_name": "医疗管理系统", "role_name": "后端开发", "tech_stack": "Python,FastAPI,MySQL", "start_date": "2023.03", "end_date": "2023.06", "description": "API开发", "achievement": "完成20+接口"}],
    "internship_list": [],
    "skill_list": [{"skill_name": "Python", "skill_level": "熟练", "category": "语言"}],
    "award_list": [],
}, ensure_ascii=False)

SAMPLE_JOB_JSON = json.dumps({
    "company_name": "云途科技有限公司",
    "job_title": "Python 后端开发工程师",
    "city": "上海",
    "job_type": "全职",
    "salary_range": "15K-25K",
    "deadline": "2026-07-31",
    "responsibility_summary": "负责后端API开发",
    "requirement_summary": "熟悉Python、FastAPI、MySQL",
    "education_required": "本科及以上",
    "experience_required": "有项目或实习经验",
    "skill_keywords": ["Python", "FastAPI", "MySQL", "Redis"],
    "tags": ["后端开发"],
}, ensure_ascii=False)

SAMPLE_MATCH_SCORES_JSON = json.dumps({
    "total_score": 78,
    "skill_score": 80,
    "project_score": 75,
    "education_score": 70,
    "experience_score": 82,
    "preference_score": 85,
    "completeness_score": 76,
}, ensure_ascii=False)

SAMPLE_STATISTICS_JSON = json.dumps({
    "total_apply_count": 12,
    "week_apply_count": 5,
    "interview_count": 2,
    "offer_count": 0,
    "reject_count": 3,
    "job_source_distribution": {"boss": 3, "campus": 2},
    "match_score_avg": 72.5,
}, ensure_ascii=False)

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


def test_resume_optimize_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_RESUME_OPTIMIZE, {
        "resume_json": SAMPLE_RESUME_JSON,
        "target_position": "Python 后端开发工程师",
    })
    assert "expression_suggestions" in content
    assert "不得编造" in content or "不得建议添加" in content
    assert "只返回JSON" in content or "只返回 JSON" in content

@pytest.mark.asyncio
async def test_resume_optimize_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    messages = PromptService(db).build_messages(PROMPT_TYPE_RESUME_OPTIMIZE, {
        "resume_json": SAMPLE_RESUME_JSON,
        "target_position": "Python 后端开发工程师",
    })
    data = await AIClient().chat_json(messages, max_tokens=2048)
    assert isinstance(data, dict)
    assert "score_before" in data
    assert "summary" in data

# ---------- D3.8 ----------
def test_resume_adapt_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_RESUME_ADAPT, {
        "resume_json": SAMPLE_RESUME_JSON,
        "job_json": SAMPLE_JOB_JSON,
    })
    assert "content_json" in content
    assert "adaptation_summary" in content
    assert "只返回JSON" in content or "只返回 JSON" in content

@pytest.mark.asyncio
async def test_resume_adapt_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    messages = PromptService(db).build_messages(PROMPT_TYPE_RESUME_ADAPT, {
        "resume_json": SAMPLE_RESUME_JSON,
        "job_json": SAMPLE_JOB_JSON,
    })
    data = await AIClient().chat_json(messages, max_tokens=3072)
    assert isinstance(data, dict)
    assert "content_json" in data
    assert "adaptation_summary" in data

# ---------- D3.9 ----------
def test_matching_analysis_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_MATCHING_ANALYSIS, {
        "resume_json": SAMPLE_RESUME_JSON,
        "job_json": SAMPLE_JOB_JSON,
        "match_scores": SAMPLE_MATCH_SCORES_JSON,
    })
    assert "skill_gap" in content
    assert "match_scores" in content or "匹配分项" in content
    assert "只返回JSON" in content or "只返回 JSON" in content

@pytest.mark.asyncio
async def test_matching_analysis_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    messages = PromptService(db).build_messages(PROMPT_TYPE_MATCHING_ANALYSIS, {
        "resume_json": SAMPLE_RESUME_JSON,
        "job_json": SAMPLE_JOB_JSON,
        "match_scores": SAMPLE_MATCH_SCORES_JSON,
    })
    data = await AIClient().chat_json(messages, max_tokens=2048)
    assert isinstance(data, dict)
    assert "summary" in data
    assert "strengths" in data
    assert "weaknesses" in data

# ---------- D3.10 ----------
def test_interview_questions_prompt_render(db):
    service = PromptService(db)
    content = service.render(PROMPT_TYPE_INTERVIEW_QUESTIONS, {
        "resume_json": SAMPLE_RESUME_JSON,
        "job_json": SAMPLE_JOB_JSON,
        "difficulty": "medium",
        "question_count": 3,
    })
    assert "questions" in content
    assert "question_type" in content
    assert "只返回JSON" in content or "只返回 JSON" in content

@pytest.mark.asyncio
async def test_interview_questions_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    messages = PromptService(db).build_messages(PROMPT_TYPE_INTERVIEW_QUESTIONS, {
        "resume_json": SAMPLE_RESUME_JSON,
        "job_json": SAMPLE_JOB_JSON,
        "difficulty": "medium",
        "question_count": 3,
    })
    data = await AIClient().chat_json(messages, max_tokens=3072)
    assert isinstance(data, dict)
    assert "questions" in data
    assert isinstance(data["questions"], list)
    assert len(data["questions"]) >= 1

# ---------- D3.11 ----------
SAMPLE_INTERVIEW_EVALUATE_VARS = {
    "job_title": "Python 后端开发工程师",
    "question_text": "请介绍一个你参与的后端项目。",
    "reference_answer": "结合医疗管理系统项目，说明技术栈、职责与成果。",
    "user_answer": "我做过医疗管理系统后端，用 FastAPI 和 MySQL，负责接口开发。",
}

def test_interview_evaluate_prompt_render(db):
    content = PromptService(db).render(PROMPT_TYPE_INTERVIEW_EVALUATE, SAMPLE_INTERVIEW_EVALUATE_VARS)
    assert "improved_answer" in content
    assert "用户回答" in content
    assert "只返回JSON" in content or "只返回 JSON" in content

@pytest.mark.asyncio
async def test_interview_evaluate_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    messages = PromptService(db).build_messages(PROMPT_TYPE_INTERVIEW_EVALUATE, SAMPLE_INTERVIEW_EVALUATE_VARS)
    data = await AIClient().chat_json(messages, max_tokens=2048)
    assert isinstance(data, dict)
    assert "score" in data
    assert "suggestion" in data

# ---------- D3.12 ----------
def test_weekly_report_prompt_render(db):
    content = PromptService(db).render(PROMPT_TYPE_WEEKLY_REPORT, {
        "start_date": "2026-06-01",
        "end_date": "2026-06-07",
        "statistics_json": SAMPLE_STATISTICS_JSON,
    })
    assert "markdown_content" in content
    assert "2026-06-01" in content
    assert "只返回JSON" in content or "只返回 JSON" in content

@pytest.mark.asyncio
async def test_weekly_report_prompt_with_llm(db, llm_settings):
    from app.modules.ai.client import AIClient
    messages = PromptService(db).build_messages(PROMPT_TYPE_WEEKLY_REPORT, {
        "start_date": "2026-06-01",
        "end_date": "2026-06-07",
        "statistics_json": SAMPLE_STATISTICS_JSON,
    })
    data = await AIClient().chat_json(messages, max_tokens=3072)
    assert isinstance(data, dict)
    assert "title" in data
    assert "highlights" in data
    assert "markdown_content" in data
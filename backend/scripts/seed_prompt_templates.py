"""
向prompt_template表中插入种子数据，用于测试
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.prompt_template import PromptTemplate

from app.modules.ai.prompt_templates.resume_generate import RESUME_GENERATE_PROMPT
from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_GENERATE
from app.modules.ai.prompt_templates.resume_parse import RESUME_PARSE_PROMPT
from app.modules.ai.prompt_templates.job_parse import JOB_PARSE_PROMPT
from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_PARSE, PROMPT_TYPE_JOB_PARSE
from app.modules.ai.prompt_constants import (
    PROMPT_TYPE_MATCHING_ANALYSIS,
    PROMPT_TYPE_RESUME_OPTIMIZE, 
    PROMPT_TYPE_RESUME_ADAPT, 
    PROMPT_TYPE_INTERVIEW_QUESTIONS, 
    PROMPT_TYPE_INTERVIEW_EVALUATE, 
    PROMPT_TYPE_WEEKLY_REPORT
    )
from app.modules.ai.prompt_templates.matching_analysis import MATCHING_ANALYSIS_PROMPT
from app.modules.ai.prompt_templates.resume_optimize import RESUME_OPTIMIZE_PROMPT
from app.modules.ai.prompt_templates.resume_adapt import RESUME_ADAPT_PROMPT
from app.modules.ai.prompt_templates.interview_questions import INTERVIEW_QUESTIONS_PROMPT
from app.modules.ai.prompt_templates.interview_evaluate import INTERVIEW_EVALUATE_PROMPT
from app.modules.ai.prompt_templates.weekly_report import WEEKLY_REPORT_PROMPT



TEST_TEMPLATE = PromptTemplate(
    template_code = "test_template",
    template_name = "测试模板",
    template_content = """你是一个JobPilot的智能简历助手。
    【角色设定】
    你只能基于用户提供的真实信息生成简历草稿，不得编造学历、项目、实习或证书。

    【输入数据】
    用户描述：{{user_description}}
    目标岗位：{{target_position}}

    【输出要求】
    1、只返回JSON，不要markdown，不要额外解释。
    2、输出语言要求：中文。
    3、JSON Schema如下：
    {
        "title": "string",
        "summary": "string",
        "skills": ["string"],
        "projects": [
            {
                "project_name": "string",
                "role_name": "string",
                "description": "string",
                "achievement": "string"
            }
        ]
    }
    4、若某字段无法获取，返回空字符串或空数组。
    """,
    version = 1,
    enabled = True, 
    created_at = datetime.utcnow(),
    updated_at = datetime.utcnow(),
)


PROMPT_DEFINITIONS = [
    {
        "template_code": PROMPT_TYPE_RESUME_GENERATE,
        "template_name": "文字生成简历",
        "template_content": RESUME_GENERATE_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_RESUME_PARSE,
        "template_name": "简历解析",
        "template_content": RESUME_PARSE_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_JOB_PARSE,
        "template_name": "岗位JD解析",
        "template_content": JOB_PARSE_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_RESUME_OPTIMIZE,
        "template_name": "简历优化",
        "template_content": RESUME_OPTIMIZE_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_RESUME_ADAPT,
        "template_name": "岗位适配",
        "template_content": RESUME_ADAPT_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_MATCHING_ANALYSIS,
        "template_name": "岗位匹配解释",
        "template_content": MATCHING_ANALYSIS_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_INTERVIEW_QUESTIONS,
        "template_name": "模拟面试题生成",
        "template_content": INTERVIEW_QUESTIONS_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_INTERVIEW_EVALUATE,
        "template_name": "面试回答评价",
        "template_content": INTERVIEW_EVALUATE_PROMPT,
        "version": 1,
    },
    {
        "template_code": PROMPT_TYPE_WEEKLY_REPORT,
        "template_name": "求职周报",
        "template_content": WEEKLY_REPORT_PROMPT,
        "version": 1,
    },
    # test_template 可保留，后续 D3.5 起继续追加
]

def _seed_one(db, definition: dict) -> None:
    existed = db.scalar(
        select(PromptTemplate).where(
            PromptTemplate.template_code == definition["template_code"],
            PromptTemplate.version == definition["version"],
        )
    )
    if existed:
        print(f"skip: {definition['template_code']} v{definition['version']}")
        return

    now = datetime.utcnow()
    db.add(
        PromptTemplate(
            template_code=definition["template_code"],
            template_name=definition["template_name"],
            template_content=definition["template_content"],
            version=definition["version"],
            enabled=True,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
    print(f"seed success: {definition['template_code']} v{definition['version']}")

def main() -> None:
    db = SessionLocal()
    try:
        print("start")
        for item in PROMPT_DEFINITIONS:
            _seed_one(db, item)
    finally:
        db.close()

if __name__ == "__main__":
    main()

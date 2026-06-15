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

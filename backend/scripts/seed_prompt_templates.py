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

def main() -> None:
    db = SessionLocal()
    try:
        existed = db.scalar(
            select(PromptTemplate).where(
                PromptTemplate.template_code == TEST_TEMPLATE.template_code,
                PromptTemplate.version == TEST_TEMPLATE.version,
            )
        )
        if existed:
            print("seed prompt template already exists, skip")
            return
        
        db.add(TEST_TEMPLATE)
        db.commit()
        print("seed prompt template success")
    finally:
        db.close()

if __name__ == "__main__":
    main()


from typing import Any

from jinja2 import Template, TemplateError, UndefinedError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.prompt_template import PromptTemplate

class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def get_template(self, template_code: str) -> PromptTemplate:
        """根据template_code、最新version和enabled读取prompt_template"""
        template = self.db.scalar(
            select(PromptTemplate)
            .where(PromptTemplate.template_code == template_code,
            PromptTemplate.enabled.is_(True))
            .order_by(PromptTemplate.version.desc())
        )

        if template is None:
            raise BusinessException(code=4044,
            message=f"prompt template not found or disabled: {template_code}",
            )
        return template

    def render(self, template_code:str, variables: dict[str, Any] | None=None) -> str:
        """渲染Jinja2模板，返回字符串"""
        template = self.get_template(template_code)
        variables = variables or {}

        try:
            rendered = Template(template.template_content).render(**variables)
        except UndefinedError as exc:
            raise BusinessException(
                code=4004,
                message=f"prompt variable missing for template:{template_code}: {exc}"
            ) from exc
        except TemplateError as exc:
            raise BusinessException(
                code=4005,
                message=f"prompt template render failed: {exc}"
            ) from exc
        
        return rendered.strip()
    
    def build_messages(
        self,
        template_code: str,
        variables: dict[str, Any] | None = None,
        *,
        role: str = "system"
        ) -> list[dict[str, str]]:
        """把渲染结果组装成OpenAI兼容的message格式"""
        content = self.render(template_code, variables)
        return [{"role": role, "content": content}]

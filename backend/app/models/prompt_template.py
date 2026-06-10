from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_template"
    __table_args__ = (
        UniqueConstraint("template_code", "version", name = "uq_prompt_template_code_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_code: Mapped[str] =mapped_column(String(128), index=True)
    template_name: Mapped[str] = mapped_column(String(128))
    template_content: Mapped[str] =mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    # false时禁用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


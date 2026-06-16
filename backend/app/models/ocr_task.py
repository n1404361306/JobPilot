from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OCRTask(Base):
    __tablename__ = "ocr_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), index=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("file_resource.id", ondelete="CASCADE"), index=True)
    task_status: Mapped[str] = mapped_column(String(32), default="pending")
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_avg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
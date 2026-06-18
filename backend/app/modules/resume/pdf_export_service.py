from pathlib import Path

import fitz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.business import ResumeVersion


class PdfExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_version(self, *, version_id: int, user_id: int, template_id: int | None = None) -> dict:
        version = self.db.scalar(
            select(ResumeVersion).where(
                ResumeVersion.id == version_id,
                ResumeVersion.user_id == user_id,
            )
        )
        if not version:
            raise BusinessException(code=4046, message="resume version not found")

        export_dir = Path("uploads") / "exports" / str(user_id)
        export_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = export_dir / f"resume-version-{version.id}.pdf"

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_textbox(
            fitz.Rect(42, 42, 553, 800),
            version.content.replace("\r\n", "\n"),
            fontsize=10,
            fontname="helv",
            lineheight=1.25,
        )
        doc.save(str(pdf_path))
        doc.close()

        return {
            "task_status": "success",
            "download_url": f"/uploads/exports/{user_id}/resume-version-{version.id}.pdf",
            "file_path": str(pdf_path),
            "template_id": template_id,
        }
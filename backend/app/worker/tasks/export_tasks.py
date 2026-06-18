from app.modules.resume.pdf_export_service import PdfExportService
from app.worker.celery_app import celery_app
from app.worker.db import worker_db_session
from app.worker.system_log import write_system_log


@celery_app.task(name="export.pdf", bind=True, max_retries=0)
def export_pdf(self, version_id: int, user_id: int, template_id: int | None = None) -> dict:
    with worker_db_session() as db:
        try:
            result = PdfExportService(db).export_version(
                version_id=version_id,
                user_id=user_id,
                template_id=template_id,
            )
            return {"status": "success", **result}
        except Exception as exc:
            write_system_log(
                db,
                level="error",
                message=f"[export.pdf] version_id={version_id}, error={exc}",
            )
            return {"status": "failed", "version_id": version_id, "error": str(exc)}
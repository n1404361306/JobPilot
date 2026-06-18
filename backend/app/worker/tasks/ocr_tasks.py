from app.modules.ocr.task_service import OCRTaskService
from app.worker.celery_app import celery_app
from app.worker.db import worker_db_session
from app.worker.system_log import write_system_log


@celery_app.task(name="ocr.extract", bind=True, max_retries=0)
def extract_ocr_text(self, task_id: int) -> dict:
    with worker_db_session() as db:
        service = OCRTaskService(db)
        try:
            task = service.run_task(task_id)
            return {
                "status": "success",
                "task_id": task.id,
                "task_status": task.task_status,
                "page_count": task.page_count,
            }
        except Exception as exc:
            write_system_log(
                db,
                level="error",
                message=f"[ocr.extract] task_id={task_id}, error={exc}",
            )
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(exc),
            }
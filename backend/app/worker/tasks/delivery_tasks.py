from app.modules.delivery.execution_service import DeliveryExecutionService
from app.worker.celery_app import celery_app
from app.worker.db import worker_db_session
from app.worker.system_log import write_system_log


@celery_app.task(name="delivery.execute", bind=True, max_retries=0)
def execute_delivery(self, task_id: int, user_id: int) -> dict:
    with worker_db_session() as db:
        try:
            task = DeliveryExecutionService(db).execute(task_id=task_id, user_id=user_id)
            return {
                "status": "success",
                "task_id": task.id,
                "task_status": task.task_status,
            }
        except Exception as exc:
            write_system_log(
                db,
                level="error",
                message=f"[delivery.execute] task_id={task_id}, error={exc}",
            )
            return {"status": "failed", "task_id": task_id, "error": str(exc)}
from app.core.exceptions import BusinessException
from app.modules.delivery.execution_service import DeliveryExecutionService
from app.worker.celery_app import celery_app
from app.worker.db import worker_db_session
from app.worker.system_log import write_system_log


@celery_app.task(name="delivery.execute", bind=True, max_retries=0)
def execute_delivery(self, task_id: int, user_id: int) -> dict:
    with worker_db_session() as db:
        service = DeliveryExecutionService(db)
        try:
            task = service.execute(task_id=task_id, user_id=user_id)
            return {
                "status": "success",
                "task_id": task.id,
                "task_status": task.task_status,
            }
        except BusinessException as exc:
            write_system_log(
                db,
                level="error",
                message=f"[delivery.execute] task_id={task_id}, error={exc.message}",
            )
            return {
                "status": "failed",
                "task_id": task_id,
                "task_status": "failed",
                "error": exc.message,
            }
        except Exception as exc:
            write_system_log(
                db,
                level="error",
                message=f"[delivery.execute] task_id={task_id}, error={exc}",
            )
            # 兜底：若仍停在 running，改为 failed
            try:
                task = service._get_task(task_id, user_id)
                if task.task_status == "running":
                    task.task_status = "failed"
                    service._add_log(
                        task,
                        user_id,
                        f"执行异常: {exc}",
                        step="error",
                        level="error",
                    )
                    db.commit()
            except Exception:
                pass
            return {
                "status": "failed",
                "task_id": task_id,
                "task_status": "failed",
                "error": str(exc),
            }
from celery import Celery

from app.core.config import get_settings

# from app.worker.tasks import ocr_tasks

settings = get_settings()

celery_app = Celery("jobpilot_worker", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="health.echo")
def echo(value: str) -> str:
    return value


# @celery_app.task(name="ai.generate")
# def generate_ai_content(prompt: str) -> dict:
#     return {"status": "success", "content": f"AI 任务已处理：{prompt[:120]}"}


# @celery_app.task(name="ocr.extract")
# def extract_ocr_text(file_path: str) -> dict:
#     return {"status": "success", "file_path": file_path, "text": "OCR 任务已创建"}


# @celery_app.task(name="export.pdf")
# def export_pdf(version_id: int) -> dict:
#     return {"status": "success", "version_id": version_id, "download_url": f"/exports/resume-{version_id}.pdf"}


# @celery_app.task(name="delivery.execute")
# def execute_delivery(task_id: int) -> dict:
#     return {"status": "success", "task_id": task_id, "message": "投递任务已完成"}


from app.worker.tasks import ocr_tasks
# from app.worker.tasks import delivery_tasks
from app.worker.tasks import delivery_tasks
from app.worker.tasks import export_tasks
from app.worker.tasks import ai_tasks


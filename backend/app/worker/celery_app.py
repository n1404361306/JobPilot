from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("jobpilot_worker", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="health.echo")
def echo(value: str) -> str:
    return value


@celery_app.task(name="ai.demo_generate")
def demo_generate(prompt: str) -> dict:
    return {"status": "success", "content": f"演示 AI 任务已处理：{prompt[:120]}"}


@celery_app.task(name="ocr.demo_extract")
def demo_ocr(file_path: str) -> dict:
    return {"status": "success", "file_path": file_path, "text": "演示 OCR 任务已创建"}


@celery_app.task(name="export.demo_pdf")
def demo_export_pdf(version_id: int) -> dict:
    return {"status": "success", "version_id": version_id, "download_url": f"/exports/resume-{version_id}.pdf"}


@celery_app.task(name="delivery.demo_execute")
def demo_delivery(task_id: int) -> dict:
    return {"status": "success", "task_id": task_id, "message": "演示模式投递任务已完成"}

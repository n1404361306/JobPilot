from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("jobpilot_worker", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="health.echo")
def echo(value: str) -> str:
    return value

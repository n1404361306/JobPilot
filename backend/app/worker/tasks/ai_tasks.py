from app.core.config import get_settings
from app.modules.ai.client import AIClient
from app.modules.ai.log_service import run_ai_with_log
from app.worker.async_runner import run_async
from app.worker.celery_app import celery_app
from app.worker.db import worker_db_session
from app.worker.system_log import write_system_log


@celery_app.task(name="ai.generate", bind=True, max_retries=0)
def generate_ai_content(
    self,
    *,
    user_id: int,
    prompt_type: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
) -> dict:
    settings = get_settings()

    async def _run() -> str:
        with worker_db_session() as db:
            result = await run_ai_with_log(
                db,
                user_id=user_id,
                prompt_type=prompt_type,
                ai_client=AIClient(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model_name=settings.ai_primary.model or settings.ai_primary_provider,
                temperature=temperature,
            )
            return result.content

    try:
        content = run_async(_run())
        return {"status": "success", "content": content}
    except Exception as exc:
        with worker_db_session() as db:
            write_system_log(
                db,
                level="error",
                message=f"[ai.generate] user_id={user_id}, error={exc}",
            )
        return {"status": "failed", "error": str(exc)}
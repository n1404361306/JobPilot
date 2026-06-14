from decimal import Decimal
import time
from typing import Any

from sqlalchemy.orm import Session

from app.models.system_log import AICallLog
from app.modules.ai.prompt_constants import AI_LOG_STATUS_FAILED, AI_LOG_STATUS_SUCCESS
from app.modules.ai.schemas import AIChatResult
from app.modules.ai.client import AIClient

class AILogService:
    def __init__(self, db: Session):
        self.db = db
    
    def log_success(
        self,
        *,
        user_id: int,
        model_name: str,
        prompt_type: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        cost_estimate: float | Decimal = 0,
        ) -> AICallLog:
        record = AICallLog(
            user_id=user_id,
            model_name=model_name,
            prompt_type=prompt_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_estimate=cost_estimate,
            status=AI_LOG_STATUS_SUCCESS,
            error_message=None,
            duration_ms=duration_ms,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def log_failure(
        self,
        *,
        user_id: int,
        model_name: str,
        prompt_type: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error_message: str,
        duration_ms: int,
        ) -> AICallLog:
        record = AICallLog(
            user_id=user_id,
            model_name=model_name,
            prompt_type=prompt_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_estimate=0,
            status=AI_LOG_STATUS_FAILED,
            error_message=error_message[:2000],
            duration_ms=duration_ms,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record


async def run_ai_with_log(
    db: Session,
    *,
    user_id: int,
    prompt_type: str,
    ai_client: AIClient,
    messages: list[dict[str,str]],
    model_name: str,
    **kwargs: Any,
) -> AIChatResult:

    log_service = AILogService(db)
    started = time.perf_counter()

    try:
        result = await ai_client.chat_with_usage(
            messages,
            **kwargs,
        )
        log_service.log_success(
            user_id=user_id,
            model_name=result.model,
            prompt_type=prompt_type,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
            duration_ms=result.usage.duration_ms,
        )
        return result
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_service.log_failure(
            user_id=user_id,
            model_name=result.model,
            prompt_type=prompt_type,
            error_message=str(exc),
            duration_ms=duration_ms
        )
        raise 



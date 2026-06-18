from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BusinessException
from app.modules.ai.client import AIClient
from app.modules.ai.log_service import run_ai_with_log
from app.modules.ai.prompt_constants import PROMPT_TYPE_JOB_PARSE
from app.modules.ai.prompt_service import PromptService
from app.modules.ocr.ocr_constants import OCR_TASK_SUCCESS
from app.modules.ocr.task_service import OCRTaskService
from app.schemas.ai import ParseJobContent, ParseJobOut

import json

class JobParseService:
    def __init__(self, db: Session):
        self.db = db
        self.prompt = PromptService(db)
        self.ai = AIClient()
        self.settings = get_settings()

    async def parse_job(
        self,
        *,
        user_id: int,
        task_id: int | None = None,
        raw_jd: str | None = None,
        source_url: str | None = None,
    ) -> ParseJobOut:
        jd = (raw_jd or "").strip()
        resolved_task_id = task_id
        source_type = "text"

        if task_id is not None:
            task = OCRTaskService(self.db).get_task_for_user(task_id, user_id)
            if task.task_status != OCR_TASK_SUCCESS:
                raise BusinessException(code=4007, message="ocr task is not completed")
            jd = (task.ocr_text or "").strip()
            source_type = "ocr"

            if not jd:
                raise BusinessException(code=4008, message="ocr text is empty")

        if not jd:
            raise BusinessException(code=4008, message="ocr text is empty")

        messages = self.prompt.build_messages(
            PROMPT_TYPE_JOB_PARSE,
            {"raw_jd": jd},
        )

        data = await run_ai_with_log(
            self.db,
            user_id=user_id,
            prompt_type=PROMPT_TYPE_JOB_PARSE,
            ai_client=self.ai,
            messages=messages,
            model_name=self.settings.ai_primary.model,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        
        try:
            data_dict = json.loads(data.content)
        except json.JSONDecodeError as exc:
            raise BusinessException(code=5002, message=f"LLM returned invalid JSON: {exc}") from exc
        
        parsed = ParseJobContent.model_validate(data_dict)

        if source_url and not parsed.source_url:
            parsed.source_url = source_url

        return ParseJobOut(
            task_id=resolved_task_id,
            source_type=source_type,
            prompt_type=PROMPT_TYPE_JOB_PARSE,
            parsed=parsed,
        )
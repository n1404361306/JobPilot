from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import BusinessException
from app.modules.ai.client import AIClient
from app.modules.ai.log_service import run_ai_with_log
from app.modules.ai.prompt_constants import PROMPT_TYPE_RESUME_PARSE
from app.modules.ai.prompt_service import PromptService
from app.modules.ocr.ocr_constants import OCR_TASK_SUCCESS
from app.modules.ocr.task_service import OCRTaskService
from app.schemas.ai import ParsedResumeContent, ParseOcrTextOut

import json

class ResumeParseService:
    def __init__(self, db: Session):
        self.db = db
        self.prompt = PromptService(db)
        self.ai = AIClient()
        self.settings = get_settings()

    async def parse_ocr_text(
        self,
        *,
        user_id: int,
        task_id: int | None = None,
        ocr_text: str | None = None,
    ) -> ParseOcrTextOut:
        text = (ocr_text or "").strip()
        resolved_task_id = task_id

        if task_id is not None:
            task = OCRTaskService(self.db).get_task_for_user(task_id, user_id)
            if task.task_status != OCR_TASK_SUCCESS:
                raise BusinessException(code=4007, message="ocr task is not completed")
            text = (task.ocr_text or "").strip()
            if not text:
                raise BusinessException(code=4008, message="ocr text is empty")

        if not text:
            raise BusinessException(code=4008, message="ocr text is empty")

        messages = self.prompt.build_messages(
            PROMPT_TYPE_RESUME_PARSE,
            {"raw_text": text, "source_type": "ocr"},
        )

        data = await run_ai_with_log(
            self.db,
            user_id=user_id,
            prompt_type=PROMPT_TYPE_RESUME_PARSE,
            ai_client=self.ai,
            messages=messages,
            model_name=self.settings.ai_primary.model,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        # run_ai_with_log 返回 AIChatResult，需再 chat_json 或在这里解析 content
        # 更简单：直接用 self.ai.chat_json(messages) + 手动 log，或扩展 run_ai_with_log 支持 chat_json
        try:
            data_dict = json.loads(data.content)
        except json.JSONDecodeError as exc:
            raise BusinessException(code=5002, message=f"LLM returned invalid JSON: {exc}") from exc
        
        parsed = ParsedResumeContent.model_validate(data_dict)
        return ParseOcrTextOut(
            task_id=resolved_task_id,
            prompt_type=PROMPT_TYPE_RESUME_PARSE,
            parsed=parsed,
        )
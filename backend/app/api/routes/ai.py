from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ok
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.modules.ai.resume_parse_service import ResumeParseService
from app.schemas.ai import ParseOcrTextRequest

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/resumes/parse-ocr-text")
async def parse_ocr_text(
    payload: ParseOcrTextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ResumeParseService(db)
    result = await service.parse_ocr_text(
        user_id=user.id,
        task_id=payload.task_id,
        ocr_text=payload.ocr_text,
    )
    return ok(result.model_dump(), "parse ocr text success")
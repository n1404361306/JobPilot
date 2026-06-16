from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.response import ok
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.modules.ocr.file_storage import save_upload_image
from app.modules.ocr.task_service import OCRTaskService
from app.schemas.ocr import OCRExtractOut, OCRTaskOut

router = APIRouter(prefix="/ocr", tags=["ocr"])


def _serialize_task(task) -> dict:
    return OCRTaskOut(
        id=task.id,
        file_id=task.file_id,
        task_status=task.task_status,
        page_count=task.page_count,
        ocr_text=task.ocr_text,
        confidence_avg=float(task.confidence_avg) if task.confidence_avg is not None else None,
        error_message=task.error_message,
        created_at=task.created_at.isoformat() if task.created_at else None,
        finished_at=task.finished_at.isoformat() if task.finished_at else None,
    ).model_dump()


@router.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_path, file_name, file_type, file_size = await save_upload_image(user_id=user.id, upload=file)

    service = OCRTaskService(db)
    file_record = service.create_file_resource(
        user_id=user.id,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
    )
    task = service.create_task(user_id=user.id, file_id=file_record.id)
    task = service.run_task(task.id)

    data = OCRExtractOut(
        task_id=task.id,
        file_id=file_record.id,
        task_status=task.task_status,
        ocr_text=task.ocr_text,
        confidence_avg=float(task.confidence_avg) if task.confidence_avg is not None else None,
        page_count=task.page_count,
    ).model_dump()
    return ok(data)


@router.get("/tasks/{task_id}")
def get_ocr_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = OCRTaskService(db).get_task_for_user(task_id, user.id)
    return ok(_serialize_task(task))
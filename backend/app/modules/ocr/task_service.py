from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.file_resource import FileResource
from app.models.ocr_task import OCRTask
from app.models.system_log import OCRLog
from app.modules.ocr.ocr_constants import (
    OCR_RELATED_TYPE,
    OCR_TASK_FAILED,
    OCR_TASK_PENDING,
    OCR_TASK_RUNNING,
    OCR_TASK_SUCCESS,
)
from app.modules.ocr.service import OCRService


class OCRTaskService:
    def __init__(self, db: Session):
        self.db = db
        self.ocr = OCRService()

    def create_file_resource(
        self,
        *,
        user_id: int,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: int,
    ) -> FileResource:
        record = FileResource(
            user_id=user_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            related_type=OCR_RELATED_TYPE,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def create_task(self, *, user_id: int, file_id: int) -> OCRTask:
        file = self.db.get(FileResource, file_id)
        if not file or file.user_id != user_id:
            raise BusinessException(code=4046, message="file not found")

        task = OCRTask(
            user_id=user_id,
            file_id=file_id,
            task_status=OCR_TASK_PENDING,
            created_at=datetime.utcnow(),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def run_task(self, task_id: int) -> OCRTask:
        task = self._get_task(task_id)
        file = self.db.get(FileResource, task.file_id)
        if file is None:
            raise BusinessException(code=4046, message="file not found")

        task.task_status = OCR_TASK_RUNNING
        self.db.add(task)
        self.db.commit()

        try:
            # result = self.ocr.extract_from_image_path(file.file_path)
            suffix = Path(file.file_path).suffix.lower()
            if suffix == ".pdf":
                result = self.ocr.extract_from_pdf_path(file.file_path)
                source_type = "pdf"
            else:
                result = self.ocr.extract_from_image_path(file.file_path)
                source_type = "image"
            task.ocr_text = result.text
            task.confidence_avg = Decimal(str(round(result.confidence_avg, 2)))
            task.page_count = result.page_count
            task.task_status = OCR_TASK_SUCCESS
            task.error_message = None
            task.finished_at = datetime.utcnow()
            self._write_ocr_log(source_type=source_type, summary=result.text, engine=result.engine)
        except Exception as exc:
            suffix = Path(file.file_path).suffix.lower()
            if suffix == ".pdf":
                # result = self.ocr.extract_from_pdf_path(file.file_path)
                source_type = "pdf"
            else:
                # result = self.ocr.extract_from_image_path(file.file_path)
                source_type = "image"
            task.task_status = OCR_TASK_FAILED
            task.error_message = str(exc)[:2000]
            task.finished_at = datetime.utcnow()
            self._write_ocr_log(source_type=source_type, summary=str(exc), engine="error", is_error=True)
            self.db.add(task)
            self.db.commit()
            raise

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task_for_user(self, task_id: int, user_id: int) -> OCRTask:
        task = self.db.get(OCRTask, task_id)
        if task is None or task.user_id != user_id:
            raise BusinessException(code=4045, message="ocr task not found")
        return task

    def _get_task(self, task_id: int) -> OCRTask:
        task = self.db.get(OCRTask, task_id)
        if task is None:
            raise BusinessException(code=4045, message="ocr task not found")
        return task

    def _write_ocr_log(self, *, source_type: str, summary: str, engine: str, is_error: bool = False) -> None:
        prefix = f"[{engine}] "
        content = summary if not is_error else f"ERROR: {summary}"
        self.db.add(
            OCRLog(
                source_type=source_type,
                result_summary=(prefix + content)[:500],
            )
        )
        self.db.commit()
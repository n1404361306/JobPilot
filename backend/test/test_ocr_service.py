from unittest.mock import patch

import pytest

from app.models.file_resource import FileResource
from app.models.ocr_task import OCRTask
from app.modules.ocr.ocr_constants import OCR_TASK_SUCCESS
from app.modules.ocr.schemas import OCRResult
from app.modules.ocr.task_service import OCRTaskService


@pytest.fixture
def sample_file(db, tmp_path):
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake-image-content")

    record = FileResource(
        user_id=1,
        file_name="sample.png",
        file_path=str(image_path),
        file_type="image/png",
        file_size=len(b"fake-image-content"),
        related_type="ocr",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_create_and_run_task_success(db, sample_file):
    service = OCRTaskService(db)
    task = service.create_task(user_id=1, file_id=sample_file.id)

    fake_result = OCRResult(
        text="张三\nPython后端开发工程师",
        confidence_avg=0.95,
        page_count=1,
        engine="mock",
    )

    with patch.object(service.ocr, "extract_from_image_path", return_value=fake_result):
        task = service.run_task(task.id)

    assert task.task_status == OCR_TASK_SUCCESS
    assert "张三" in (task.ocr_text or "")
    assert float(task.confidence_avg or 0) == pytest.approx(0.95)


def test_get_task_for_user(db, sample_file):
    service = OCRTaskService(db)
    task = service.create_task(user_id=1, file_id=sample_file.id)

    found = service.get_task_for_user(task.id, 1)
    assert found.id == task.id

    with pytest.raises(Exception):
        service.get_task_for_user(task.id, 999)

@pytest.fixture
def sample_pdf_file(db, tmp_path):
    pdf_path = tmp_path / "resume.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    record = FileResource(
        user_id=1,
        file_name="resume.pdf",
        file_path=str(pdf_path),
        file_type="application/pdf",
        file_size=10,
        related_type="ocr",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_run_task_pdf_success(db, sample_pdf_file):
    service = OCRTaskService(db)
    task = service.create_task(user_id=1, file_id=sample_pdf_file.id)

    fake_result = OCRResult(
        text="李四\nJava开发",
        confidence_avg=0.92,
        page_count=2,
        engine="pymupdf-text",
    )

    with patch.object(service.ocr, "extract_from_pdf_path", return_value=fake_result):
        task = service.run_task(task.id)

    assert task.task_status == OCR_TASK_SUCCESS
    assert task.page_count == 2
    assert "李四" in (task.ocr_text or "")
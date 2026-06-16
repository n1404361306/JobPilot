from pydantic import BaseModel


class OCRTaskOut(BaseModel):
    id: int
    file_id: int
    task_status: str
    page_count: int
    ocr_text: str | None = None
    confidence_avg: float | None = None
    error_message: str | None = None
    created_at: str | None = None
    finished_at: str | None = None

    model_config = {"from_attributes": True}


class OCRExtractOut(BaseModel):
    task_id: int
    file_id: int
    task_status: str
    ocr_text: str | None = None
    confidence_avg: float | None = None
    page_count: int
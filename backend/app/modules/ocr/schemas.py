from pydantic import BaseModel

class OCRResult(BaseModel):
    text: str
    confidence_avg: float
    page_count: int
    engine: str
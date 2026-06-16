from functools import lru_cache

from app.core.config import get_settings
from app.core.exceptions import BusinessException
from app.modules.ocr.schemas import OCRResult


class OCRService:
    def __init__(self):
        self.settings = get_settings()

    def extract_from_image_path(self, image_path: str) -> OCRResult:
        engine = self.settings.ocr_engine.lower()
        if engine == "tesseract":
            return self._extract_with_tesseract(image_path)
        if engine == "paddleocr":
            return self._extract_with_paddleocr(image_path)
        raise BusinessException(code=5004, message=f"unsupported ocr engine: {engine}")

    def _extract_with_paddleocr(self, image_path: str) -> OCRResult:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise BusinessException(code=5005, message="paddleocr not installed") from exc

        ocr = _get_paddle_ocr(self.settings.ocr_lang)
        raw = ocr.predict(image_path)

        lines: list[str] = []
        scores: list[float] = []
        for page in raw or []:
            lines.extend(page["rec_texts"])
            scores.extend(float(s) for s in page["rec_scores"])
        
        text = "\n".join(lines).strip()
        avg = sum(scores) / len(scores) if scores else 0.0
        return OCRResult(text=text, confidence_avg=avg, page_count=1, engine="paddleocr")

    def _extract_with_tesseract(self, image_path: str) -> OCRResult:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise BusinessException(code=5005, message="tesseract dependencies not installed") from exc

        text = pytesseract.image_to_string(Image.open(image_path), lang="chi_sim+eng")
        return OCRResult(text=text.strip(), confidence_avg=0.0, page_count=1, engine="tesseract")


@lru_cache
def _get_paddle_ocr(lang: str):
    from paddleocr import PaddleOCR
    return PaddleOCR(
        lang=lang, 
        ocr_version="PP-OCRv4",
        use_textline_orientation=True,
        enable_mkldnn=False
        )
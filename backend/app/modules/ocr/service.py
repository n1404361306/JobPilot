from functools import lru_cache
from pathlib import Path


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


    def extract_from_pdf_path(self, pdf_path: str) -> OCRResult:
        import fitz

        doc = fitz.open(pdf_path)
        page_count = len(doc)
        if page_count == 0:
            raise BusinessException(code=5006, message="empty pdf")
        # 1) 先尝试直接抽文本（文字版 PDF）
        page_texts: list[str] = []
        for page in doc:
            t = page.get_text("text").strip()
            if t:
                page_texts.append(t)
        merged = "\n\n".join(page_texts)
        # 去掉空白后的有效字符数
        effective_len = len("".join(merged.split()))
        MIN_TEXT_CHARS = 80  # 可放到 config：OCR_PDF_MIN_TEXT_CHARS
        if effective_len >= MIN_TEXT_CHARS:
            doc.close()
            return OCRResult(
                text=merged,
                confidence_avg=1.0,
                page_count=page_count,
                engine="pymupdf-text",
            )
        # 2) 图片版 PDF：逐页转图 + OCR
        all_text_parts: list[str] = []
        all_scores: list[float] = []
        engine = self.settings.ocr_engine.lower()
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 清晰度
            tmp_png = Path(pdf_path).with_suffix(f".page{i}.png")
            pix.save(str(tmp_png))
            try:
                page_result = self.extract_from_image_path(str(tmp_png))
                if page_result.text.strip():
                    all_text_parts.append(page_result.text.strip())
                if page_result.confidence_avg > 0:
                    all_scores.append(page_result.confidence_avg)
            finally:
                tmp_png.unlink(missing_ok=True)
        doc.close()
        text = "\n\n".join(all_text_parts).strip()
        avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
        return OCRResult(
            text=text,
            confidence_avg=avg,
            page_count=page_count,
            engine=f"{engine}+pymupdf",
        )

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
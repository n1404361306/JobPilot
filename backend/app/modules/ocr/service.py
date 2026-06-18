import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import BusinessException
from app.modules.ocr.schemas import OCRResult

PDF_MIN_TEXT_CHARS = 80

# Windows 常见 Tesseract 安装路径
_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


class OCRService:
    def __init__(self):
        self.settings = get_settings()

    def extract_from_image_path(self, image_path: str) -> OCRResult:
        preferred = self.settings.ocr_engine.lower()
        engines = self._engine_order(preferred)
        errors: list[str] = []

        for engine in engines:
            try:
                if engine == "tesseract":
                    return self._extract_with_tesseract(image_path)
                if engine == "rapidocr":
                    return self._extract_with_rapidocr(image_path)
                if engine == "paddleocr":
                    return self._extract_with_paddleocr(image_path)
            except BusinessException as exc:
                errors.append(str(exc.message))
            except Exception as exc:
                errors.append(f"{engine}: {exc}")

        detail = "；".join(errors) if errors else "未知 OCR 错误"
        raise BusinessException(
            code=5005,
            message=(
                "OCR 识别失败。建议优先使用可复制文字的文字版 PDF 或 Word（.docx）。"
                "扫描版 PDF/图片需要服务端配置可用的 OCR 引擎。"
                f"详情：{detail}"
            ),
        )

    def _engine_order(self, preferred: str) -> list[str]:
        fallback = ["tesseract", "rapidocr", "paddleocr"]
        if preferred not in fallback:
            preferred = "tesseract"
        ordered = [preferred] + [item for item in fallback if item != preferred]
        return ordered

    def extract_from_pdf_path(self, pdf_path: str) -> OCRResult:
        import fitz

        doc = fitz.open(pdf_path)
        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise BusinessException(code=5006, message="PDF 文件为空")

        merged = self._extract_pdf_text_layer(doc)
        effective_len = len("".join(merged.split()))

        if effective_len >= PDF_MIN_TEXT_CHARS:
            doc.close()
            return OCRResult(
                text=merged,
                confidence_avg=1.0,
                page_count=page_count,
                engine="pymupdf-text",
            )

        if effective_len > 0:
            doc.close()
            return OCRResult(
                text=merged,
                confidence_avg=0.8,
                page_count=page_count,
                engine="pymupdf-text-partial",
            )

        all_text_parts: list[str] = []
        all_scores: list[float] = []
        ocr_engine = self.settings.ocr_engine.lower()
        try:
            for index, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                tmp_png = Path(pdf_path).with_suffix(f".page{index}.png")
                pix.save(str(tmp_png))
                try:
                    page_result = self.extract_from_image_path(str(tmp_png))
                    if page_result.text.strip():
                        all_text_parts.append(page_result.text.strip())
                    if page_result.confidence_avg > 0:
                        all_scores.append(page_result.confidence_avg)
                finally:
                    tmp_png.unlink(missing_ok=True)
        finally:
            doc.close()

        text = "\n\n".join(all_text_parts).strip()
        if not text:
            raise BusinessException(
                code=5005,
                message="未能从 PDF 提取文字，请确认文件清晰或改用文字版 PDF/Word",
            )

        avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
        return OCRResult(
            text=text,
            confidence_avg=avg,
            page_count=page_count,
            engine=f"{ocr_engine}+pymupdf",
        )

    def _extract_pdf_text_layer(self, doc) -> str:
        parts: list[str] = []
        for page in doc:
            text = page.get_text("text", sort=True).strip()
            if not text:
                blocks = page.get_text("blocks")
                block_lines = [
                    str(block[4]).strip()
                    for block in blocks
                    if len(block) > 4 and str(block[4]).strip()
                ]
                text = "\n".join(block_lines).strip()
            if text:
                parts.append(text)
        return "\n\n".join(parts).strip()

    def _extract_with_rapidocr(self, image_path: str) -> OCRResult:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except Exception as exc:
            raise BusinessException(
                code=5005,
                message=(
                    "RapidOCR 不可用。请确认已执行 pip install rapidocr-onnxruntime，"
                    "并安装匹配当前 Python/Windows 的 onnxruntime 运行依赖。"
                    f"原始错误：{exc}"
                ),
            ) from exc

        engine = _get_rapid_ocr()
        result, _elapsed = engine(image_path)
        if not result:
            raise BusinessException(code=5005, message="rapidocr 未识别到文字")

        lines: list[str] = []
        scores: list[float] = []
        for item in result:
            if len(item) >= 2 and str(item[1]).strip():
                lines.append(str(item[1]).strip())
            if len(item) >= 3:
                try:
                    scores.append(float(item[2]))
                except (TypeError, ValueError):
                    pass

        text = "\n".join(lines).strip()
        if not text:
            raise BusinessException(code=5005, message="rapidocr 未识别到文字")
        avg = sum(scores) / len(scores) if scores else 0.0
        return OCRResult(text=text, confidence_avg=avg, page_count=1, engine="rapidocr")

    def _extract_with_paddleocr(self, image_path: str) -> OCRResult:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise BusinessException(code=5005, message="未安装 paddleocr") from exc

        ocr = _get_paddle_ocr(self.settings.ocr_lang)
        raw = ocr.predict(image_path)

        lines: list[str] = []
        scores: list[float] = []
        for page in raw or []:
            lines.extend(page["rec_texts"])
            scores.extend(float(score) for score in page["rec_scores"])

        text = "\n".join(lines).strip()
        if not text:
            raise BusinessException(code=5005, message="paddleocr 未识别到文字")
        avg = sum(scores) / len(scores) if scores else 0.0
        return OCRResult(text=text, confidence_avg=avg, page_count=1, engine="paddleocr")

    def _extract_with_tesseract(self, image_path: str) -> OCRResult:
        cmd = _resolve_tesseract_cmd(self.settings.tesseract_cmd)
        if not cmd:
            raise BusinessException(code=5005, message="Tesseract executable not found")

        args = [cmd, image_path, "stdout", "-l", _resolve_tesseract_lang()]
        tessdata_dir = _project_tessdata_dir()
        if tessdata_dir:
            args.extend(["--tessdata-dir", str(tessdata_dir)])

        completed = subprocess.run(args, capture_output=True, check=False)
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        if completed.returncode != 0:
            raise BusinessException(code=5005, message=f"Tesseract OCR failed: {stderr or completed.returncode}")

        text = completed.stdout.decode("utf-8", errors="replace").strip()
        if not text:
            raise BusinessException(code=5005, message="tesseract did not recognize text")
        return OCRResult(text=text, confidence_avg=0.0, page_count=1, engine="tesseract")

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise BusinessException(code=5005, message="未安装 pytesseract 或 Pillow") from exc

        cmd = _resolve_tesseract_cmd(self.settings.tesseract_cmd)
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd

        try:
            text = pytesseract.image_to_string(
                Image.open(image_path),
                lang=_resolve_tesseract_lang(),
                config=_resolve_tesseract_config(),
            )
        except pytesseract.TesseractNotFoundError as exc:
            raise BusinessException(
                code=5005,
                message=(
                    "服务端未找到 Tesseract 可执行文件。"
                    "请在服务端安装 Tesseract，或在 .env 中设置 TESSERACT_CMD 指向 tesseract 可执行文件"
                ),
            ) from exc

        text = text.strip()
        if not text:
            raise BusinessException(code=5005, message="tesseract 未识别到文字")
        return OCRResult(text=text, confidence_avg=0.0, page_count=1, engine="tesseract")


_paddle_ocr_instance = None
_paddle_ocr_disabled = False
_rapid_ocr_instance = None
_rapid_ocr_disabled = False


def _resolve_tesseract_cmd(configured: str | None) -> str | None:
    if configured and Path(configured).is_file():
        return configured

    which = shutil.which("tesseract")
    if which:
        return which

    for candidate in _TESSERACT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate

    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd and Path(env_cmd).is_file():
        return env_cmd

    return None


def _project_tessdata_dir() -> Path | None:
    tessdata_dir = Path(__file__).resolve().parents[3] / "tessdata"
    if (tessdata_dir / "chi_sim.traineddata").is_file():
        return tessdata_dir
    return None


def _resolve_tesseract_lang() -> str:
    tessdata_dir = _project_tessdata_dir()
    if tessdata_dir and (tessdata_dir / "eng.traineddata").is_file():
        return "chi_sim+eng"
    if tessdata_dir:
        return "chi_sim"
    return "chi_sim+eng"


def _resolve_tesseract_config() -> str:
    tessdata_dir = _project_tessdata_dir()
    if not tessdata_dir:
        return ""
    return f'--tessdata-dir "{tessdata_dir}"'


def _get_paddle_ocr(lang: str):
    global _paddle_ocr_instance, _paddle_ocr_disabled
    if _paddle_ocr_disabled:
        raise BusinessException(code=5005, message="paddleocr 当前不可用，请改用 tesseract")
    if _paddle_ocr_instance is not None:
        return _paddle_ocr_instance
    try:
        from paddleocr import PaddleOCR

        _paddle_ocr_instance = PaddleOCR(
            lang=lang,
            ocr_version="PP-OCRv4",
            use_textline_orientation=True,
            enable_mkldnn=False,
            use_doc_unwarping=False,
            use_doc_orientation_classify=False,
        )
        return _paddle_ocr_instance
    except Exception as exc:
        _paddle_ocr_disabled = True
        msg = str(exc)
        if "PDX has already been initialized" in msg:
            msg = "Paddle 运行时重复初始化失败（Windows 环境常见），已跳过"
        raise BusinessException(code=5005, message=f"paddleocr 初始化失败：{msg}") from exc


def _get_rapid_ocr():
    global _rapid_ocr_instance, _rapid_ocr_disabled
    if _rapid_ocr_disabled:
        raise BusinessException(code=5005, message="rapidocr 当前不可用，请改用 tesseract")
    if _rapid_ocr_instance is not None:
        return _rapid_ocr_instance
    try:
        from rapidocr_onnxruntime import RapidOCR

        _rapid_ocr_instance = RapidOCR()
        return _rapid_ocr_instance
    except Exception as exc:
        _rapid_ocr_disabled = True
        raise BusinessException(code=5005, message=f"rapidocr 初始化失败：{exc}") from exc

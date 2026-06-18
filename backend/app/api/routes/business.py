import json
import re
import tempfile
import urllib.request
import uuid
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.resume.template_validation import validate_template_content
from app.core.exceptions import BusinessException
from app.core.response import ok
from app.db.session import get_db
from app.deps.auth import get_current_user, require_permissions
from app.models.business import (
    Application,
    ApplicationStatusHistory,
    DeliveryProfile,
    DeliveryTask,
    DeliveryTaskLog,
    Job,
    JobSearchReport,
    MatchReport,
    Resume,
    ResumeTemplate,
    ResumeVersion,
)
from app.models.user import User
from app.schemas.business import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationStatusHistoryOut,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    DeliveryProfileOut,
    DeliveryProfilePayload,
    DeliveryTaskCreate,
    DeliveryTaskLogOut,
    DeliveryTaskOut,
    JobBatchConfirmRequest,
    JobBatchImportRequest,
    JobCreate,
    JobImportTextRequest,
    JobImportUrlRequest,
    JobOut,
    JobUpdate,
    MatchCalculateRequest,
    MatchReportOut,
    ReportOut,
    ResumeCreate,
    ResumeOut,
    ResumeRenderRequest,
    ResumeTemplateCreate,
    ResumeTemplateOut,
    ResumeTemplateSelectRequest,
    ResumeTemplateUpdate,
    ResumeUpdate,
    ResumeVersionCreate,
    ResumeVersionOut,
    ResumeVersionUpdate,
)
from app.modules.resume.document_extractor import extract_resume_text
from app.core.config import get_settings
from app.modules.ai.client import AIClient
from app.modules.ai.log_service import run_ai_with_log
from app.modules.ai.prompt_service import PromptService

router = APIRouter(tags=["business"])


def _dump(model, schema):
    return schema.model_validate(model, from_attributes=True).model_dump()


def _set_fields(model, payload, fields: tuple[str, ...]) -> None:
    data = payload.model_dump(exclude_unset=True)
    for field in fields:
        if field in data:
            setattr(model, field, data[field])


RESUME_FORM_MARKER = "<!--RESUME_FORM"

VALID_APPLICATION_STATUSES = frozenset(
    {
        "pending",
        "submitted",
        "screening",
        "written",
        "tech_first",
        "tech_second",
        "hr_interview",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
    }
)
INTERVIEW_PIPELINE_STATUSES = frozenset(
    {"written", "tech_first", "tech_second", "hr_interview", "interview", "offer"}
)
MATCH_SCORE_RANGE_ORDER = ("0-59", "60-79", "80-100")


def _normalize_application_status(status: str | None) -> str:
    normalized = (status or "pending").strip()
    return normalized if normalized in VALID_APPLICATION_STATUSES else "pending"


def _application_status_counter(applications) -> Counter:
    return Counter(_normalize_application_status(item.status) for item in applications)


def _interview_pipeline_count(status_counts: Counter) -> int:
    return sum(status_counts.get(status, 0) for status in INTERVIEW_PIPELINE_STATUSES)


def _match_score_ranges(reports) -> dict[str, int]:
    return {
        "0-59": sum(1 for report in reports if report.score < 60),
        "60-79": sum(1 for report in reports if 60 <= report.score < 80),
        "80-100": sum(1 for report in reports if report.score >= 80),
    }


def _active_job_count(jobs) -> int:
    return sum(1 for job in jobs if job.status == "active")


def _can_use_template(template: ResumeTemplate, user: User) -> bool:
    return template.enabled and (template.user_id is None or template.user_id == user.id or template.is_public)


def _ensure_template_access(db: Session, template_key: str, user: User) -> None:
    if not template_key.startswith("custom:"):
        return
    try:
        template_id = int(template_key.split(":", 1)[1])
    except ValueError as exc:
        raise BusinessException(code=4007, message="invalid template id") from exc
    template = db.get(ResumeTemplate, template_id)
    if not template or not _can_use_template(template, user):
        raise BusinessException(code=4031, message="template not allowed")


def _apply_template_key_to_resume_content(content: str, template_key: str) -> str:
    marker_index = content.rfind(RESUME_FORM_MARKER)
    if marker_index == -1:
        snapshot = {
            "basic_info": {"name": "", "phone": "", "email": "", "github": "", "website": "", "location": "", "photo": ""},
            "job_intention": "",
            "summary": content,
            "skillsText": {"languages": "", "backend": "", "database": "", "ai": "", "tools": "", "language_ability": ""},
            "education": [],
            "internships": [],
            "projects": [],
            "researchText": "",
            "awardsText": "",
            "certificatesText": "",
            "open_source": "",
            "interests": "",
            "self_evaluation": "",
            "missingText": "",
            "templateId": template_key,
        }
        return f"{content.strip()}\n\n{RESUME_FORM_MARKER}\n{json.dumps(snapshot, ensure_ascii=False)}\n-->"

    display_content = content[:marker_index].strip()
    json_start = content.find("\n", marker_index) + 1
    json_end = content.rfind("\n-->")
    snapshot: dict = {}
    if json_start > 0 and json_end > json_start:
        try:
            parsed = json.loads(content[json_start:json_end])
            if isinstance(parsed, dict):
                snapshot = parsed
        except json.JSONDecodeError:
            snapshot = {}
    snapshot["templateId"] = template_key
    return f"{display_content}\n\n{RESUME_FORM_MARKER}\n{json.dumps(snapshot, ensure_ascii=False)}\n-->"


def _get_resume(db: Session, resume_id: int, user_id: int) -> Resume:
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
    if not resume:
        raise BusinessException(code=4042, message="resume not found")
    return resume


def _get_job(db: Session, job_id: int, user_id: int) -> Job:
    job = db.scalar(select(Job).where(Job.id == job_id, Job.user_id == user_id))
    if not job:
        raise BusinessException(code=4043, message="job not found")
    return job


def _get_application(db: Session, application_id: int, user_id: int) -> Application:
    application = db.scalar(select(Application).where(Application.id == application_id, Application.user_id == user_id))
    if not application:
        raise BusinessException(code=4044, message="application not found")
    return application


def _clear_default_resume(db: Session, user_id: int) -> None:
    resumes = db.scalars(select(Resume).where(Resume.user_id == user_id, Resume.is_default.is_(True))).all()
    for resume in resumes:
        resume.is_default = False
        db.add(resume)


def _validate_resume_reference(db: Session, resume_id: int | None, user_id: int) -> None:
    if resume_id is not None:
        _get_resume(db, resume_id, user_id)


def _get_version(db: Session, version_id: int, user_id: int) -> ResumeVersion:
    version = db.scalar(select(ResumeVersion).where(ResumeVersion.id == version_id, ResumeVersion.user_id == user_id))
    if not version:
        raise BusinessException(code=4046, message="resume version not found")
    return version


def _get_delivery_task(db: Session, task_id: int, user_id: int) -> DeliveryTask:
    task = db.scalar(select(DeliveryTask).where(DeliveryTask.id == task_id, DeliveryTask.user_id == user_id))
    if not task:
        raise BusinessException(code=4048, message="delivery task not found")
    return task


def _extract_keywords(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9+#.]+|[\u4e00-\u9fff]{2,}", text.lower())
    stopwords = {"and", "the", "with", "for", "岗位", "要求", "负责", "经验", "公司", "项目", "能力"}
    return {token for token in tokens if token not in stopwords and len(token) > 1}


def _label_value(line: str, labels: tuple[str, ...]) -> str | None:
    normalized = line.replace("：", ":")
    for label in labels:
        pattern = rf"^\s*{re.escape(label)}\s*[:：]\s*(.+)$"
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" -\t")
            return value or None
    return None


def _clean_job_text(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.M)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return text.strip()


_JOB_TYPE_LINES = frozenset(
    {"日常实习", "校招", "全职", "兼职", "暑期实习", "寒假实习", "实习", "日常"}
)
_LISTING_HEADER_PATTERN = re.compile(r"^全部.*职位|^校招职位")
_MEITUAN_JOB_START_PATTERN = re.compile(
    r"\n(?=[^\n]{2,80}\n(?:日常实习|校招|全职|兼职|暑期实习|寒假实习|实习)\n)"
)


def _render_prompt_or_default(db: Session, template_code: str, variables: dict, default_prompt: str) -> str:
    try:
        return PromptService(db).render(template_code, variables)
    except Exception:
        return default_prompt


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|li|h[1-6]|tr)>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return _clean_job_text(text)


def _fetch_url_text(source_url: str) -> str:
    if not re.match(r"^https?://", source_url, flags=re.IGNORECASE):
        raise BusinessException(code=4006, message="URL 必须以 http:// 或 https:// 开头")
    request = urllib.request.Request(source_url, headers={"User-Agent": "JobPilot/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read(1024 * 1024)
            content_type = response.headers.get("content-type", "")
    except Exception as exc:
        raise BusinessException(code=5005, message=f"URL 抓取失败：{exc}") from exc

    charset_match = re.search(r"charset=([\w-]+)", content_type, flags=re.IGNORECASE)
    charset = charset_match.group(1) if charset_match else "utf-8"
    html = raw.decode(charset, errors="ignore")
    return _strip_html(html)


def _infer_job_from_text(text: str, source_url: str | None = None) -> dict:
    text = _clean_job_text(text)
    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
    if lines and _LISTING_HEADER_PATTERN.match(lines[0]):
        lines = lines[1:]
    first = lines[0] if lines else "导入岗位"
    company = "待补充公司"
    title = ""
    location = None
    salary_range = None
    deadline = None
    job_type = None
    tags: list[str] = []

    if len(lines) >= 2 and lines[1] in _JOB_TYPE_LINES:
        title = lines[0]
        job_type = lines[1]
        company = "待补充公司"
        description_start = 2
        for idx in range(2, min(len(lines), 12)):
            line = lines[idx]
            if line.startswith("更新于"):
                continue
            if line in ("岗位职责", "岗位要求", "任职要求", "【岗位职责】"):
                description_start = idx
                break
            if not location and (
                line.endswith("市")
                or "、" in line
                or re.fullmatch(r"[A-Za-z\u4e00-\u9fff\s]+", line)
            ):
                location = line
                continue
            if company == "待补充公司":
                company = line
                continue
            description_start = idx
            break
        description = "\n".join(lines[description_start:])
        return {
            "title": title[:128],
            "company": company[:128],
            "location": location[:128] if location else None,
            "salary_range": salary_range,
            "source_type": "manual" if source_url is None else "url",
            "job_type": job_type[:64] if job_type else None,
            "deadline": deadline,
            "tags": "、".join(tags)[:512] if tags else None,
            "is_favorite": False,
            "import_batch_id": None,
            "source_url": source_url,
            "description": description or text,
            "status": "active",
        }

    for line in lines[:40]:
        title = title or _label_value(line, ("岗位名称", "职位名称", "招聘岗位", "岗位", "职位", "title", "job title")) or ""
        company = _label_value(line, ("公司名称", "公司", "企业", "单位", "company")) or company
        location = location or _label_value(line, ("工作地点", "办公地点", "地点", "城市", "location", "city"))
        salary_range = salary_range or _label_value(line, ("薪资范围", "薪资", "薪酬", "待遇", "salary"))
        deadline = deadline or _label_value(line, ("截止时间", "截止日期", "投递截止", "deadline"))

        if not salary_range:
            salary_match = re.search(r"(\d+(?:\.\d+)?\s*[kK千万]-\s*\d+(?:\.\d+)?\s*[kK千万](?:\s*[·xX*]\s*\d{1,2})?)", line)
            if salary_match:
                salary_range = salary_match.group(1).replace(" ", "")
        for keyword in ("Java", "Python", "Go", "C++", "Spring", "FastAPI", "Vue", "React", "MySQL", "Redis", "算法", "测试", "后端", "前端", "AI"):
            if keyword.lower() in line.lower() and keyword not in tags:
                tags.append(keyword)

    if not title:
        for line in lines[:12]:
            if "公司" in line or len(line) > 80:
                continue
            if any(key in line for key in ("工程师", "开发", "产品", "运营", "算法", "测试", "实习", "经理", "专员")):
                title = line.replace("岗位", "").replace("职位", "").replace("：", ":").split(":")[-1].strip()
                break

    title = (title or first)[:128]
    company = company[:128]
    return {
        "title": title,
        "company": company,
        "location": location[:128] if location else None,
        "salary_range": salary_range[:128] if salary_range else None,
        "source_type": "manual" if source_url is None else "url",
        "job_type": job_type[:64] if job_type else None,
        "deadline": deadline[:64] if deadline else None,
        "tags": "、".join(tags)[:512] if tags else None,
        "is_favorite": False,
        "import_batch_id": None,
        "source_url": source_url,
        "description": text,
        "status": "active",
    }


JOB_JSON_SYSTEM_PROMPT = (
    "你是岗位 JD 信息抽取助手。请把用户提供的招聘信息抽取为严格 JSON 对象。"
    "只能使用原文中明确出现或可以直接归纳的信息，不要编造公司、地点和薪资。"
    "必须返回合法 JSON，不要 Markdown，不要解释。"
)


def _job_json_user_prompt(text: str, source_url: str | None = None) -> str:
    return (
        "请输出如下 JSON 结构：\n"
        "{\n"
        '  "title": "",\n'
        '  "company": "",\n'
        '  "location": "",\n'
        '  "salary_range": "",\n'
        '  "job_type": "",\n'
        '  "deadline": "",\n'
        '  "description": "",\n'
        '  "requirements": [],\n'
        '  "responsibilities": [],\n'
        '  "tags": []\n'
        "}\n"
        "要求：title、company 尽量从原文抽取；description 保留一份清晰完整的岗位描述；"
        "requirements/responsibilities/tags 用数组。没有明确内容时用空字符串或空数组。\n"
        f"来源链接：{source_url or ''}\n"
        f"岗位文本：\n{text}"
    )


def _as_text_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in re.split(r"[；;\n]", value) if item.strip()]
    return []


def _normalize_ai_job_data(data: dict, source_text: str, source_url: str | None) -> dict:
    fallback = _infer_job_from_text(source_text, source_url)
    title = str(data.get("title") or fallback["title"]).strip()[:128]
    company = str(data.get("company") or fallback["company"]).strip()[:128]
    location = str(data.get("location") or fallback.get("location") or "").strip()
    salary_range = str(data.get("salary_range") or fallback.get("salary_range") or "").strip()
    job_type = str(data.get("job_type") or fallback.get("job_type") or "").strip()
    deadline = str(data.get("deadline") or fallback.get("deadline") or "").strip()
    description = str(data.get("description") or "").strip() or source_text
    responsibilities = _as_text_list(data.get("responsibilities"))
    requirements = _as_text_list(data.get("requirements"))
    tags = _as_text_list(data.get("tags"))

    parts = [description]
    if responsibilities:
        parts.extend(["", "岗位职责", *[f"- {item}" for item in responsibilities]])
    if requirements:
        parts.extend(["", "岗位要求", *[f"- {item}" for item in requirements]])
    if tags:
        parts.extend(["", f"岗位标签：{'、'.join(tags)}"])

    return {
        "title": title or fallback["title"],
        "company": company or fallback["company"],
        "location": location[:128] if location else fallback.get("location"),
        "salary_range": salary_range[:128] if salary_range else fallback.get("salary_range"),
        "job_type": job_type[:64] if job_type else fallback.get("job_type"),
        "deadline": deadline[:64] if deadline else fallback.get("deadline"),
        "tags": "、".join(tags)[:512] if tags else fallback.get("tags"),
        "source_url": source_url,
        "description": _clean_job_text("\n".join(parts)),
        "status": "active",
    }


async def _parse_job_with_ai_or_rule(db: Session, user_id: int, text: str, source_url: str | None = None) -> dict:
    text = _clean_job_text(text)
    if not text:
        raise BusinessException(code=4008, message="岗位文本为空")

    settings = get_settings()
    try:
        system_prompt = _render_prompt_or_default(
            db,
            "job_parse",
            {"source_text": text, "source_url": source_url or ""},
            JOB_JSON_SYSTEM_PROMPT,
        )
        result = await run_ai_with_log(
            db,
            user_id=user_id,
            prompt_type="job_import_parse",
            ai_client=AIClient(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": _job_json_user_prompt(text, source_url)},
            ],
            model_name=settings.ai_primary.model or settings.ai_primary_provider,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        parsed = json.loads(result.content)
        if not isinstance(parsed, dict):
            raise ValueError("AI returned non-object JSON")
        return _normalize_ai_job_data(parsed, text, source_url)
    except Exception:
        return _infer_job_from_text(text, source_url)


def _find_duplicate_job(db: Session, user_id: int, data: dict) -> Job | None:
    return db.scalar(
        select(Job).where(
            Job.user_id == user_id,
            Job.title == data["title"],
            Job.company == data["company"],
        )
    )


def _create_imported_job(db: Session, user_id: int, data: dict) -> Job:
    duplicate = _find_duplicate_job(db, user_id, data)
    if duplicate:
        return duplicate
    job = Job(user_id=user_id, **data)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _split_batch_jobs(text: str, separator: str | None = None) -> list[str]:
    text = _clean_job_text(text)
    lines = text.splitlines()
    if lines and _LISTING_HEADER_PATTERN.match(lines[0].strip()):
        text = "\n".join(lines[1:]).strip()

    if separator:
        chunks = text.split(separator)
    else:
        meituan_chunks = _MEITUAN_JOB_START_PATTERN.split(text)
        if len(meituan_chunks) > 1:
            chunks = meituan_chunks
        elif "\n\n" in text:
            chunks = re.split(r"\n\s*\n+", text)
        else:
            chunks = re.split(
                r"\n\s*(?:---+|===+|###|岗位\s*\d+[:：]?|职位\s*\d+[:：]?)\s*\n",
                text,
            )
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) >= 10]


JOB_BATCH_JSON_SYSTEM_PROMPT = (
    "你是 JobPilot 的通用批量岗位解析助手。用户会粘贴来自不同招聘网站、表格、列表页、"
    "聊天记录或多个完整 JD 混合在一起的文本。你的任务分两步：第一步识别每个独立岗位的边界，"
    "第二步只基于该岗位对应原文抽取结构化字段。"
    "不要依赖单一格式；不要因为没有空行、没有序号、没有分隔线就把多个岗位合并。"
    "也不要把同一个完整 JD 内部的职责、要求、更新时间、岗位类别、工作地点等字段误拆成多个岗位。"
    "必须只返回合法 JSON 对象，不要 Markdown，不要解释。"
)


def _job_batch_json_user_prompt(text: str, separator: str | None = None) -> str:
    separator_hint = f"用户提供的自定义分隔符：{separator}\n" if separator else ""
    return (
        "请把下面的批量岗位文本解析为 JSON：\n"
        "{\n"
        '  "jobs": [\n'
        "    {\n"
        '      "title": "",\n'
        '      "company": "",\n'
        '      "location": "",\n'
        '      "salary_range": "",\n'
        '      "source_url": "",\n'
        '      "source_type": "batch_text",\n'
        '      "job_type": "",\n'
        '      "deadline": "",\n'
        '      "tags": "",\n'
        '      "is_favorite": false,\n'
        '      "description": "",\n'
        '      "status": "active"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "通用拆分协议：\n"
        "1. 先通读全文，判断文本属于哪种形态：多个完整 JD、招聘网站列表页、表格/CSV 复制、"
        "序号列表、无分隔符重复块、聊天记录摘录，或这些格式的混合。\n"
        "2. jobs 数组中每个元素必须对应一个独立岗位；岗位边界以“新的岗位标题/职位名称/岗位编号/招聘条目开始”为准。\n"
        "3. 常见边界信号包括但不限于：序号、分隔线、空行、岗位名称行、职位名称字段、公司+岗位组合、"
        "日期/类别/城市/业务线重复块、表格新行、URL 新行、薪资+地点+公司组合。\n"
        "4. 对无空行的列表页，要识别重复结构。例如“岗位名 → 更新日期 → 类别 → 城市 → 业务线”"
        "反复出现时，每次新岗位名都是一个新岗位。\n"
        "5. 对完整 JD，不要把“岗位职责”“任职要求”“工作地点”“更新时间”“职位类别”等小节拆成新岗位；"
        "它们属于当前岗位的 description。\n"
        "6. 如果只有岗位标题列表，也要每个标题生成一条岗位，缺失字段留空或用“待补充公司”。\n"
        "7. 如果某段文字无法判断是新岗位还是当前岗位详情，优先并入当前岗位 description，避免过度拆分。\n\n"
        "字段抽取协议：\n"
        "1. 每条岗位只能使用自己的原文片段抽取字段，不要串用其他岗位的信息。\n"
        "2. title 必须是岗位/职位名称；company 没有明确公司时填“待补充公司”。\n"
        "3. location、salary_range、deadline、job_type、source_url 没有明确内容时用空字符串。\n"
        "4. tags 可用逗号或顿号分隔原文出现的类别、技术关键词、业务线、岗位方向，不要扩展同义词。\n"
        "5. description 必须保留该岗位的原始片段或清晰摘要，作为用户检查依据，不要包含其他岗位内容。\n"
        "6. 不得编造薪资、地点、截止日期、职责、公司名或技术要求。\n\n"
        f"{separator_hint}"
        f"批量岗位文本：\n{text}"
    )


def _normalize_batch_ai_job_data(data: dict, source_text: str) -> dict:
    title = str(data.get("title") or "").strip()[:128] or "待补充岗位"
    company = str(data.get("company") or "").strip()[:128] or "待补充公司"
    location = str(data.get("location") or "").strip()
    salary_range = str(data.get("salary_range") or "").strip()
    source_url = str(data.get("source_url") or "").strip()
    job_type = str(data.get("job_type") or "").strip()
    deadline = str(data.get("deadline") or "").strip()
    description = str(data.get("description") or "").strip() or source_text
    tags = data.get("tags")
    if isinstance(tags, list):
        tag_text = "、".join(str(item).strip() for item in tags if str(item).strip())
    else:
        tag_text = str(tags or "").strip()

    return {
        "title": title,
        "company": company,
        "location": location[:128] if location else None,
        "salary_range": salary_range[:128] if salary_range else None,
        "source_url": source_url[:512] if source_url else None,
        "source_type": "batch_text",
        "job_type": job_type[:64] if job_type else None,
        "deadline": deadline[:64] if deadline else None,
        "tags": tag_text[:512] if tag_text else None,
        "is_favorite": bool(data.get("is_favorite", False)),
        "import_batch_id": None,
        "description": _clean_job_text(description),
        "status": str(data.get("status") or "active"),
    }


async def _parse_batch_jobs_with_ai(db: Session, user_id: int, text: str, separator: str | None = None) -> list[dict]:
    text = _clean_job_text(text)
    if not text:
        raise BusinessException(code=4008, message="岗位文本为空")

    settings = get_settings()
    try:
        result = await run_ai_with_log(
            db,
            user_id=user_id,
            prompt_type="job_batch_import_parse",
            ai_client=AIClient(),
            messages=[
                {"role": "system", "content": JOB_BATCH_JSON_SYSTEM_PROMPT},
                {"role": "user", "content": _job_batch_json_user_prompt(text, separator)},
            ],
            model_name=settings.ai_primary.model or settings.ai_primary_provider,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        parsed = json.loads(result.content)
    except Exception as exc:
        raise BusinessException(code=5006, message=f"AI 批量岗位解析失败：{exc}") from exc

    jobs = parsed.get("jobs") if isinstance(parsed, dict) else None
    if not isinstance(jobs, list) or not jobs:
        raise BusinessException(code=5006, message="AI 未返回可导入的岗位列表")

    normalized_jobs: list[dict] = []
    for item in jobs:
        if isinstance(item, dict):
            item_text = str(item.get("description") or item.get("title") or text)
            normalized_jobs.append(_normalize_batch_ai_job_data(item, item_text))

    if not normalized_jobs:
        raise BusinessException(code=5006, message="AI 未返回有效岗位")
    return normalized_jobs


async def _extract_upload_text(file: UploadFile) -> tuple[str, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"}:
        raise BusinessException(code=4006, message="不支持的文件类型，请上传 PDF、DOCX、TXT、MD、PNG、JPG 或 WEBP")

    raw = await file.read()
    if not raw:
        raise BusinessException(code=4008, message="上传文件为空")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        text, source_type, _engine = extract_resume_text(tmp_path)
        return text, source_type
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _build_match_report(resume: Resume, job: Job) -> dict:
    resume_keywords = _extract_keywords(resume.content)
    job_keywords = _extract_keywords(" ".join([job.title, job.company, job.description or ""]))
    overlap = sorted(resume_keywords & job_keywords)
    missing = sorted(job_keywords - resume_keywords)[:10]
    coverage = len(overlap) / max(len(job_keywords), 1)
    completeness = min(len(resume.content) / 600, 1)
    score = int(min(95, 35 + coverage * 45 + completeness * 20))
    strengths = "、".join(overlap[:8]) or "简历已有基础经历，可继续补充岗位关键词。"
    gaps = "、".join(missing[:8]) or "未发现明显关键词缺口。"
    suggestions = "建议将岗位 JD 中的核心技能前置到技能栈，并用项目经历说明对应成果。"
    summary = f"当前匹配度 {score} 分，关键词覆盖 {len(overlap)}/{len(job_keywords)}，适合用于初筛投递前优化。"
    return {
        "score": score,
        "summary": summary,
        "strengths": strengths,
        "gaps": gaps,
        "suggestions": suggestions,
    }


MATCH_JSON_SYSTEM_PROMPT = (
    "你是求职匹配分析助手。请基于候选人简历和岗位 JD，输出严格 JSON。"
    "分析要具体、可执行，不能编造候选人没有的经历。必须返回合法 JSON，不要 Markdown。"
)


def _match_json_user_prompt(resume: Resume, job: Job, rule_report: dict) -> str:
    return (
        "请输出如下 JSON 结构：\n"
        "{\n"
        '  "score": 0,\n'
        '  "summary": "",\n'
        '  "strengths": "",\n'
        '  "gaps": "",\n'
        '  "suggestions": ""\n'
        "}\n"
        "要求：score 为 0-100 整数；summary 用 1-2 句话说明整体匹配度；"
        "strengths 写匹配优势；gaps 写主要差距；suggestions 写简历优化和投递建议。"
        "规则初评分只作为参考，AI 可以根据语义微调，但不要偏离太大。\n\n"
        f"规则初评分：{rule_report.get('score')}\n"
        f"规则优势：{rule_report.get('strengths')}\n"
        f"规则差距：{rule_report.get('gaps')}\n\n"
        f"简历标题：{resume.title}\n"
        f"简历内容：\n{resume.content[:6000]}\n\n"
        f"岗位：{job.company} - {job.title}\n"
        f"地点：{job.location or ''}\n"
        f"薪资：{job.salary_range or ''}\n"
        f"岗位描述：\n{(job.description or '')[:6000]}"
    )


def _normalize_match_ai_data(data: dict, rule_report: dict) -> dict:
    try:
        score = int(float(data.get("score", rule_report["score"])))
    except (TypeError, ValueError):
        score = int(rule_report["score"])
    score = max(0, min(100, score))

    return {
        "score": score,
        "summary": str(data.get("summary") or rule_report["summary"]).strip(),
        "strengths": str(data.get("strengths") or rule_report["strengths"]).strip(),
        "gaps": str(data.get("gaps") or rule_report["gaps"]).strip(),
        "suggestions": str(data.get("suggestions") or rule_report["suggestions"]).strip(),
    }


async def _build_match_report_with_ai_or_rule(db: Session, user_id: int, resume: Resume, job: Job) -> dict:
    rule_report = _build_match_report(resume, job)
    settings = get_settings()
    try:
        result = await run_ai_with_log(
            db,
            user_id=user_id,
            prompt_type="matching_analysis",
            ai_client=AIClient(),
            messages=[
                {"role": "system", "content": MATCH_JSON_SYSTEM_PROMPT},
                {"role": "user", "content": _match_json_user_prompt(resume, job, rule_report)},
            ],
            model_name=settings.ai_primary.model or settings.ai_primary_provider,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        parsed = json.loads(result.content)
        if not isinstance(parsed, dict):
            raise ValueError("AI returned non-object JSON")
        return _normalize_match_ai_data(parsed, rule_report)
    except Exception:
        return rule_report


def _create_status_history(
    db: Session,
    *,
    application_id: int,
    user_id: int,
    from_status: str | None,
    to_status: str,
    note: str | None = None,
) -> None:
    db.add(
        ApplicationStatusHistory(
            application_id=application_id,
            user_id=user_id,
            from_status=from_status,
            to_status=to_status,
            note=note,
        )
    )


@router.get("/resumes")
def list_resumes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resumes = db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.id.desc())).all()
    return ok([_dump(resume, ResumeOut) for resume in resumes])


@router.post("/resumes")
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.is_default:
        _clear_default_resume(db, user.id)
    resume = Resume(user_id=user.id, **payload.model_dump())
    db.add(resume)
    db.commit()
    db.refresh(resume)
    version = ResumeVersion(
        resume_id=resume.id,
        user_id=user.id,
        version_name="初始版本",
        content=resume.content,
        structured_data=None,
    )
    db.add(version)
    db.commit()
    return ok(_dump(resume, ResumeOut), "resume created")


@router.get("/resumes/{resume_id}")
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = _get_resume(db, resume_id, user.id)
    return ok(_dump(resume, ResumeOut))


@router.put("/resumes/{resume_id}")
def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = _get_resume(db, resume_id, user.id)
    if payload.is_default is True:
        _clear_default_resume(db, user.id)
    _set_fields(resume, payload, ("title", "content", "file_url", "is_default"))
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return ok(_dump(resume, ResumeOut), "resume updated")


@router.delete("/resumes/{resume_id}")
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = _get_resume(db, resume_id, user.id)
    db.delete(resume)
    db.commit()
    return ok(message="resume deleted")


@router.get("/resumes/{resume_id}/versions")
def list_resume_versions(
    resume_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_resume(db, resume_id, user.id)
    versions = db.scalars(
        select(ResumeVersion)
        .where(ResumeVersion.resume_id == resume_id, ResumeVersion.user_id == user.id)
        .order_by(ResumeVersion.id.desc())
    ).all()
    return ok([_dump(version, ResumeVersionOut) for version in versions])


@router.post("/resumes/{resume_id}/versions")
def create_resume_version(
    resume_id: int,
    payload: ResumeVersionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = _get_resume(db, resume_id, user.id)
    version = ResumeVersion(
        resume_id=resume.id,
        user_id=user.id,
        version_name=payload.version_name,
        content=payload.content,
        structured_data=payload.structured_data,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return ok(_dump(version, ResumeVersionOut), "resume version created")


@router.get("/resume-versions/{version_id}")
def get_resume_version(
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    version = _get_version(db, version_id, user.id)
    return ok(_dump(version, ResumeVersionOut))


@router.put("/resume-versions/{version_id}")
def update_resume_version(
    version_id: int,
    payload: ResumeVersionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    version = _get_version(db, version_id, user.id)
    _set_fields(version, payload, ("version_name", "content", "structured_data"))
    db.add(version)
    db.commit()
    db.refresh(version)
    return ok(_dump(version, ResumeVersionOut), "resume version updated")


@router.post("/resume-versions/{version_id}/copy")
def copy_resume_version(
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    version = _get_version(db, version_id, user.id)
    copied = ResumeVersion(
        resume_id=version.resume_id,
        user_id=user.id,
        version_name=f"{version.version_name} 副本",
        content=version.content,
        structured_data=version.structured_data,
    )
    db.add(copied)
    db.commit()
    db.refresh(copied)
    return ok(_dump(copied, ResumeVersionOut), "resume version copied")


@router.post("/resume-versions/{version_id}/render")
def render_resume_version(
    version_id: int,
    payload: ResumeRenderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    version = _get_version(db, version_id, user.id)
    template = db.get(ResumeTemplate, payload.template_id) if payload.template_id else None
    if template and template.user_id not in (None, user.id):
        raise BusinessException(code=4031, message="template not allowed")
    title = template.name if template else "默认简历模板"
    html = (
        Template(template.content).render(content=version.content, resume_content=version.content, title=title)
        if template
        else f"<article class='resume-preview'><h1>{title}</h1><pre>{version.content}</pre></article>"
    )
    return ok({"html": html, "version_id": version.id, "template_id": payload.template_id})
    title = template.name if template else "默认简历模板"
    html = (
        "<article class='resume-preview'>"
        f"<h1>{title}</h1>"
        f"<pre>{version.content}</pre>"
        "</article>"
    )
    return ok({"html": html, "version_id": version.id, "template_id": payload.template_id})


@router.post("/resume-versions/{version_id}/export-pdf")
def export_resume_version_pdf(
    version_id: int,
    payload: ResumeRenderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    version = _get_version(db, version_id, user.id)
    export_dir = Path("uploads") / "exports" / str(user.id)
    export_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = export_dir / f"resume-version-{version.id}.pdf"
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_textbox(
        fitz.Rect(42, 42, 553, 800),
        version.content.replace("\r\n", "\n"),
        fontsize=10,
        fontname="helv",
        lineheight=1.25,
    )
    doc.save(str(pdf_path))
    doc.close()
    return ok(
        {
            "task_status": "success",
            "download_url": f"/uploads/exports/{user.id}/resume-version-{version.id}.pdf",
            "file_path": str(pdf_path),
            "template_id": payload.template_id,
        },
        "pdf exported",
    )
    return ok(
        {
            "task_status": "created",
            "download_url": f"/api/resume-versions/{version.id}/rendered-preview.pdf",
            "template_id": payload.template_id,
        },
        "pdf export task created",
    )


@router.get("/resume-templates")
def list_resume_templates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    templates = db.scalars(
        select(ResumeTemplate)
        .where(
            ResumeTemplate.enabled.is_(True),
            (ResumeTemplate.user_id.is_(None)) | (ResumeTemplate.user_id == user.id) | (ResumeTemplate.is_public.is_(True)),
        )
        .order_by(ResumeTemplate.id.desc())
    ).all()
    return ok([_dump(template, ResumeTemplateOut) for template in templates])


@router.get("/resume-templates/manage")
def manage_resume_templates(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["business:templates:write"])),
):
    templates = db.scalars(select(ResumeTemplate).order_by(ResumeTemplate.id.desc())).all()
    return ok([_dump(template, ResumeTemplateOut) for template in templates])


@router.post("/resume-templates")
def create_resume_template(
    payload: ResumeTemplateCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["business:templates:write"])),
):
    data = payload.model_dump()
    data["is_system"] = True
    data["is_public"] = True
    template = ResumeTemplate(**data, user_id=None)
    db.add(template)
    db.commit()
    db.refresh(template)
    return ok(_dump(template, ResumeTemplateOut), "template created")


@router.put("/resume-templates/{template_id}")
def update_resume_template(
    template_id: int,
    payload: ResumeTemplateUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["business:templates:write"])),
):
    template = db.get(ResumeTemplate, template_id)
    if not template:
        raise BusinessException(code=4045, message="resume template not found")
    _set_fields(template, payload, ("name", "description", "content", "enabled", "is_public"))
    db.add(template)
    db.commit()
    db.refresh(template)
    return ok(_dump(template, ResumeTemplateOut), "template updated")


@router.delete("/resume-templates/{template_id}")
def delete_resume_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["business:templates:write"])),
):
    template = db.get(ResumeTemplate, template_id)
    if not template:
        raise BusinessException(code=4045, message="resume template not found")
    db.delete(template)
    db.commit()
    return ok(message="template deleted")


@router.post("/resume-templates/upload")
async def upload_resume_template(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    description: str | None = Form(default=None),
    is_public: bool = Form(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    raw = await file.read()
    try:
        content = validate_template_content(raw.decode("utf-8", errors="ignore"))
    except ValueError as exc:
        raise BusinessException(code=4006, message=str(exc)) from exc
    template = ResumeTemplate(
        name=(name or file.filename or "用户模板")[:128],
        description=(description or "用户上传模板")[:255],
        content=content or "{{content}}",
        enabled=True,
        user_id=user.id,
        is_system=False,
        is_public=is_public,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return ok(_dump(template, ResumeTemplateOut), "template uploaded")


@router.post("/resume-templates/mine")
def create_my_resume_template(
    payload: ResumeTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        content = validate_template_content(payload.content)
    except ValueError as exc:
        raise BusinessException(code=4006, message=str(exc)) from exc
    template = ResumeTemplate(
        name=payload.name[:128],
        description=(payload.description or "用户自制模板")[:255],
        content=content,
        enabled=True,
        user_id=user.id,
        is_system=False,
        is_public=payload.is_public,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return ok(_dump(template, ResumeTemplateOut), "template created")


@router.get("/resume-templates/{template_id}")
def get_resume_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = db.get(ResumeTemplate, template_id)
    if not template or not _can_use_template(template, user):
        raise BusinessException(code=4045, message="resume template not found")
    return ok(_dump(template, ResumeTemplateOut))


@router.put("/resume-templates/{template_id}/mine")
def update_my_resume_template(
    template_id: int,
    payload: ResumeTemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = db.get(ResumeTemplate, template_id)
    if not template or template.user_id != user.id:
        raise BusinessException(code=4045, message="resume template not found")
    if payload.content is not None:
        try:
            payload.content = validate_template_content(payload.content)
        except ValueError as exc:
            raise BusinessException(code=4006, message=str(exc)) from exc
    _set_fields(template, payload, ("name", "description", "content", "enabled", "is_public"))
    db.add(template)
    db.commit()
    db.refresh(template)
    return ok(_dump(template, ResumeTemplateOut), "template updated")


@router.post("/resumes/{resume_id}/template")
def select_resume_template(
    resume_id: int,
    payload: ResumeTemplateSelectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = db.get(Resume, resume_id)
    if not resume or resume.user_id != user.id:
        raise BusinessException(code=4041, message="resume not found")
    _ensure_template_access(db, payload.template_id, user)
    resume.content = _apply_template_key_to_resume_content(resume.content, payload.template_id)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return ok(_dump(resume, ResumeOut), "template selected")


@router.post("/resume-templates/{template_id}/copy")
def copy_resume_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = db.get(ResumeTemplate, template_id)
    if not template:
        raise BusinessException(code=4045, message="resume template not found")
    if template.user_id not in (None, user.id):
        raise BusinessException(code=4031, message="template not allowed")
    copied = ResumeTemplate(
        name=f"{template.name} 副本",
        description=template.description,
        content=template.content,
        enabled=True,
        user_id=user.id,
        is_system=False,
        is_public=False,
        copied_from_id=template.id,
    )
    db.add(copied)
    db.commit()
    db.refresh(copied)
    return ok(_dump(copied, ResumeTemplateOut), "template copied")


@router.get("/jobs")
def list_jobs(
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    favorite: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Job).where(Job.user_id == user.id)
    if status:
        stmt = stmt.where(Job.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where((Job.title.like(pattern)) | (Job.company.like(pattern)))
    if favorite is not None:
        stmt = stmt.where(Job.is_favorite.is_(favorite))
    jobs = db.scalars(stmt.order_by(Job.id.desc())).all()
    return ok([_dump(job, JobOut) for job in jobs])


@router.post("/jobs")
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = Job(user_id=user.id, **payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return ok(_dump(job, JobOut), "job created")


@router.post("/jobs/import/text")
async def import_job_from_text(
    payload: JobImportTextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await _parse_job_with_ai_or_rule(db, user.id, payload.text, payload.source_url)
    data["source_type"] = "text"
    duplicate = _find_duplicate_job(db, user.id, data)
    job = duplicate or _create_imported_job(db, user.id, data)
    if duplicate:
        return ok(_dump(job, JobOut), "job already exists")
    return ok(_dump(job, JobOut), "job imported")


@router.post("/jobs/import/url")
async def import_job_from_url(
    payload: JobImportUrlRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    text = payload.text.strip() if payload.text and payload.text.strip() else _fetch_url_text(payload.source_url)
    if not text:
        raise BusinessException(code=4008, message="URL 页面中未提取到有效岗位文本")
    data = await _parse_job_with_ai_or_rule(db, user.id, text, payload.source_url)
    data["source_type"] = "url"
    if data["title"] == "导入岗位":
        data["title"] = "URL 导入岗位"
    duplicate = _find_duplicate_job(db, user.id, data)
    job = duplicate or _create_imported_job(db, user.id, data)
    if duplicate:
        return ok(_dump(job, JobOut), "job already exists")
    return ok(_dump(job, JobOut), "url job imported")


@router.post("/jobs/import/batch-text/preview")
async def preview_jobs_from_batch_text(
    payload: JobBatchImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    jobs = await _parse_batch_jobs_with_ai(db, user.id, payload.text, payload.separator)
    return ok({"count": len(jobs), "jobs": jobs}, "batch jobs parsed")

    chunks = _split_batch_jobs(payload.text, payload.separator)
    if not chunks:
        raise BusinessException(code=4008, message="未识别到可导入的岗位块")
    jobs: list[dict] = []
    for chunk in chunks:
        data = await _parse_job_with_ai_or_rule(db, user.id, chunk)
        data["source_type"] = "batch_text"
        data["import_batch_id"] = None
        jobs.append(data)
    return ok({"count": len(jobs), "jobs": jobs}, "batch jobs parsed")


@router.post("/jobs/import/batch-text")
async def import_jobs_from_batch_text(
    payload: JobBatchConfirmRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    batch_id = uuid.uuid4().hex[:16]
    jobs: list[dict] = []
    for item in payload.jobs:
        data = item.model_dump()
        data["source_type"] = "batch_text"
        data["import_batch_id"] = batch_id
        job = _create_imported_job(db, user.id, data)
        jobs.append(_dump(job, JobOut))
    return ok({"batch_id": batch_id, "count": len(jobs), "jobs": jobs}, "batch jobs imported")


@router.post("/jobs/import/file")
async def import_job_from_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    text, _source_type = await _extract_upload_text(file)
    data = await _parse_job_with_ai_or_rule(db, user.id, text)
    data["source_type"] = "file"
    duplicate = _find_duplicate_job(db, user.id, data)
    job = duplicate or _create_imported_job(db, user.id, data)
    if duplicate:
        return ok(_dump(job, JobOut), "job already exists")
    return ok(_dump(job, JobOut), "file job imported")


@router.post("/jobs/import/image")
async def import_job_from_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise BusinessException(code=4006, message="截图导入仅支持 PNG、JPG、JPEG、WEBP")
    text, _source_type = await _extract_upload_text(file)
    data = await _parse_job_with_ai_or_rule(db, user.id, text)
    data["source_type"] = "image"
    duplicate = _find_duplicate_job(db, user.id, data)
    job = duplicate or _create_imported_job(db, user.id, data)
    if duplicate:
        return ok(_dump(job, JobOut), "job already exists")
    return ok(_dump(job, JobOut), "image job imported")


@router.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = _get_job(db, job_id, user.id)
    return ok(_dump(job, JobOut))


@router.put("/jobs/{job_id}")
def update_job(
    job_id: int,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = _get_job(db, job_id, user.id)
    _set_fields(
        job,
        payload,
        ("title", "company", "location", "salary_range", "source_url", "description", "status"),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return ok(_dump(job, JobOut), "job updated")


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = _get_job(db, job_id, user.id)
    db.delete(job)
    db.commit()
    return ok(message="job deleted")


@router.get("/applications")
def list_applications(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Application).where(Application.user_id == user.id)
    if status:
        stmt = stmt.where(Application.status == status)
    applications = db.scalars(stmt.order_by(Application.id.desc())).all()
    return ok([_dump(application, ApplicationOut) for application in applications])


@router.post("/applications")
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_job(db, payload.job_id, user.id)
    _validate_resume_reference(db, payload.resume_id, user.id)
    data = payload.model_dump()
    if data["status"] == "submitted" and data["applied_at"] is None:
        data["applied_at"] = datetime.utcnow()
    application = Application(user_id=user.id, **data)
    db.add(application)
    db.commit()
    db.refresh(application)
    _create_status_history(
        db,
        application_id=application.id,
        user_id=user.id,
        from_status=None,
        to_status=application.status,
        note="创建投递记录",
    )
    db.commit()
    return ok(_dump(application, ApplicationOut), "application created")


@router.get("/applications/kanban")
def application_kanban(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    applications = db.scalars(select(Application).where(Application.user_id == user.id).order_by(Application.id.desc())).all()
    grouped: dict[str, list[dict]] = {}
    for application in applications:
        grouped.setdefault(application.status, []).append(_dump(application, ApplicationOut))
    return ok(grouped)


@router.get("/applications/{application_id}")
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = _get_application(db, application_id, user.id)
    return ok(_dump(application, ApplicationOut))


@router.put("/applications/{application_id}")
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = _get_application(db, application_id, user.id)
    data = payload.model_dump(exclude_unset=True)
    if "resume_id" in data:
        _validate_resume_reference(db, data["resume_id"], user.id)
    if data.get("status") == "submitted" and data.get("applied_at") is None and application.applied_at is None:
        data["applied_at"] = datetime.utcnow()
    old_status = application.status
    for field, value in data.items():
        setattr(application, field, value)
    if "status" in data and data["status"] != old_status:
        _create_status_history(
            db,
            application_id=application.id,
            user_id=user.id,
            from_status=old_status,
            to_status=data["status"],
            note=data.get("note"),
        )
    db.add(application)
    db.commit()
    db.refresh(application)
    return ok(_dump(application, ApplicationOut), "application updated")


@router.delete("/applications/{application_id}")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = _get_application(db, application_id, user.id)
    db.delete(application)
    db.commit()
    return ok(message="application deleted")


@router.post("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = _get_application(db, application_id, user.id)
    old_status = application.status
    application.status = payload.status
    if payload.status == "submitted" and application.applied_at is None:
        application.applied_at = datetime.utcnow()
    _create_status_history(
        db,
        application_id=application.id,
        user_id=user.id,
        from_status=old_status,
        to_status=payload.status,
        note=payload.note,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return ok(_dump(application, ApplicationOut), "application status updated")


@router.get("/applications/{application_id}/history")
def list_application_history(
    application_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_application(db, application_id, user.id)
    history = db.scalars(
        select(ApplicationStatusHistory)
        .where(
            ApplicationStatusHistory.application_id == application_id,
            ApplicationStatusHistory.user_id == user.id,
        )
        .order_by(ApplicationStatusHistory.id.desc())
    ).all()
    return ok([_dump(item, ApplicationStatusHistoryOut) for item in history])


@router.post("/matching/calculate")
async def calculate_match(
    payload: MatchCalculateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = _get_resume(db, payload.resume_id, user.id)
    job = _get_job(db, payload.job_id, user.id)
    data = await _build_match_report_with_ai_or_rule(db, user.id, resume, job)
    report = MatchReport(user_id=user.id, resume_id=resume.id, job_id=job.id, **data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return ok(_dump(report, MatchReportOut), "match calculated")


@router.get("/matching/reports/{report_id}")
def get_match_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = db.scalar(select(MatchReport).where(MatchReport.id == report_id, MatchReport.user_id == user.id))
    if not report:
        raise BusinessException(code=4047, message="match report not found")
    return ok(_dump(report, MatchReportOut))


@router.get("/statistics/overview")
def statistics_overview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resumes = db.scalars(select(Resume).where(Resume.user_id == user.id)).all()
    jobs = db.scalars(select(Job).where(Job.user_id == user.id)).all()
    applications = db.scalars(select(Application).where(Application.user_id == user.id)).all()
    reports = db.scalars(select(MatchReport).where(MatchReport.user_id == user.id)).all()
    status_counts = _application_status_counter(applications)
    city_counts = Counter(job.location or "未填写" for job in jobs)
    avg_match = round(sum(item.score for item in reports) / len(reports), 1) if reports else 0
    return ok(
        {
            "resume_count": len(resumes),
            "job_count": len(jobs),
            "active_job_count": _active_job_count(jobs),
            "application_count": len(applications),
            "match_report_count": len(reports),
            "average_match_score": avg_match,
            "status_counts": dict(status_counts),
            "city_counts": dict(city_counts),
        }
    )


@router.get("/statistics/applications")
def statistics_applications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    applications = db.scalars(select(Application).where(Application.user_id == user.id)).all()
    status_counts = _application_status_counter(applications)
    total = len(applications)
    interview_count = _interview_pipeline_count(status_counts)
    offer_count = status_counts.get("offer", 0)
    return ok(
        {
            "total": total,
            "status_counts": dict(status_counts),
            "interview_count": interview_count,
            "offer_count": offer_count,
            "interview_conversion_rate": round(interview_count / total, 4) if total else 0,
            "offer_conversion_rate": round(offer_count / total, 4) if total else 0,
        }
    )


@router.get("/statistics/jobs")
def statistics_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    jobs = db.scalars(select(Job).where(Job.user_id == user.id)).all()
    tag_counts: Counter[str] = Counter()
    for job in jobs:
        for tag in re.split(r"[、,，;\s]+", job.tags or ""):
            if tag:
                tag_counts[tag] += 1
    return ok(
        {
            "total": len(jobs),
            "active_count": _active_job_count(jobs),
            "source_counts": dict(Counter(job.source_type or "manual" for job in jobs)),
            "type_counts": dict(Counter(job.job_type or "未分类" for job in jobs)),
            "city_counts": dict(Counter(job.location or "未填写" for job in jobs)),
            "favorite_count": sum(1 for job in jobs if job.is_favorite),
            "tag_counts": dict(tag_counts),
        }
    )


@router.get("/statistics/matches")
def statistics_matches(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reports = db.scalars(select(MatchReport).where(MatchReport.user_id == user.id)).all()
    score_ranges = _match_score_ranges(reports)
    return ok(
        {
            "total": len(reports),
            "average_score": round(sum(report.score for report in reports) / len(reports), 1) if reports else 0,
            "score_ranges": score_ranges,
            "latest": [_dump(report, MatchReportOut) for report in sorted(reports, key=lambda item: item.id, reverse=True)[:10]],
        }
    )


@router.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reports = db.scalars(
        select(JobSearchReport).where(JobSearchReport.user_id == user.id).order_by(JobSearchReport.id.desc())
    ).all()
    return ok([_dump(report, ReportOut) for report in reports])


def _build_weekly_report_context(db: Session, user_id: int) -> dict:
    resumes = db.scalars(select(Resume).where(Resume.user_id == user_id)).all()
    jobs = db.scalars(select(Job).where(Job.user_id == user_id)).all()
    applications = db.scalars(select(Application).where(Application.user_id == user_id)).all()
    reports = db.scalars(select(MatchReport).where(MatchReport.user_id == user_id)).all()
    status_counts = _application_status_counter(applications)
    return {
        "overview": {
            "resume_count": len(resumes),
            "job_count": len(jobs),
            "active_job_count": _active_job_count(jobs),
            "application_count": len(applications),
            "match_report_count": len(reports),
            "average_match_score": round(sum(r.score for r in reports) / len(reports), 1) if reports else 0,
        },
        "application_status_counts": dict(status_counts),
        "job_source_counts": dict(Counter(job.source_type or "manual" for job in jobs)),
        "job_city_counts": dict(Counter(job.location or "未填写" for job in jobs)),
        "match_score_ranges": _match_score_ranges(reports),
    }


WEEKLY_REPORT_DEFAULT_PROMPT = (
    "你是求职复盘顾问。基于用户真实统计数据生成中文求职总结。"
    "不要编造未发生的投递、面试或 Offer。"
    "输出纯中文段落，不要使用 markdown 符号（如 # * ** - ###）。"
    "不要输出模板占位符，例如 [您的姓名]、[开始日期] 等方括号文本。"
    "直接写总结正文，可用换行分段。"
)


def _format_summary_from_json(data: dict, user: User, start_date: date, end_date: date) -> str:
    lines = [
        f"求职者：{user.username}",
        f"复盘周期：{start_date.isoformat()} - {end_date.isoformat()}",
        "",
    ]
    title = str(data.get("title") or "").strip()
    if title:
        lines.extend([title, ""])
    highlights = data.get("highlights") or []
    if isinstance(highlights, list) and highlights:
        lines.append("本周亮点")
        for item in highlights:
            if str(item).strip():
                lines.append(f"· {str(item).strip()}")
        lines.append("")
    apply_summary = str(data.get("apply_summary") or "").strip()
    if apply_summary:
        lines.extend(["投递概况", apply_summary, ""])
    interview_summary = str(data.get("interview_summary") or "").strip()
    if interview_summary:
        lines.extend(["面试与反馈", interview_summary, ""])
    suggestions = data.get("improvement_suggestions") or []
    if isinstance(suggestions, list) and suggestions:
        lines.append("改进建议")
        for item in suggestions:
            if str(item).strip():
                lines.append(f"· {str(item).strip()}")
        lines.append("")
    next_plan = data.get("next_week_plan") or []
    if isinstance(next_plan, list) and next_plan:
        lines.append("下周计划")
        for item in next_plan:
            if str(item).strip():
                lines.append(f"· {str(item).strip()}")
    return "\n".join(lines).strip()


async def _generate_weekly_report_with_ai(db: Session, user: User) -> str:
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    context = _build_weekly_report_context(db, user.id)
    statistics_json = json.dumps(context, ensure_ascii=False)
    settings = get_settings()
    system_prompt = _render_prompt_or_default(
        db,
        "weekly_report",
        {
            "statistics_json": statistics_json,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "username": user.username,
        },
        WEEKLY_REPORT_DEFAULT_PROMPT,
    )
    result = await run_ai_with_log(
        db,
        user_id=user.id,
        prompt_type="weekly_report",
        ai_client=AIClient(),
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"求职者：{user.username}\n"
                    f"复盘周期：{start_date.isoformat()} - {end_date.isoformat()}\n"
                    f"统计数据 JSON：\n{statistics_json}"
                ),
            },
        ],
        model_name=settings.ai_primary.model or settings.ai_primary_provider,
        temperature=0.2,
    )
    raw = result.content.strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            markdown_content = str(parsed.get("markdown_content") or "").strip()
            if markdown_content:
                return _strip_markdown(markdown_content)
            return _strip_markdown(_format_summary_from_json(parsed, user, start_date, end_date))
    except json.JSONDecodeError:
        pass
    return _strip_markdown(raw)


@router.post("/reports/weekly")
async def create_weekly_report(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await _generate_weekly_report_with_ai(db, user)
    report = JobSearchReport(user_id=user.id, title="AI 求职总结", content=content, report_type="weekly")
    db.add(report)
    db.commit()
    db.refresh(report)
    return ok(_dump(report, ReportOut), "weekly report created")


@router.delete("/reports/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = db.scalar(
        select(JobSearchReport).where(JobSearchReport.id == report_id, JobSearchReport.user_id == user.id)
    )
    if not report:
        raise BusinessException(code=4049, message="report not found")
    db.delete(report)
    db.commit()
    return ok(None, "report deleted")


@router.get("/delivery/profiles/me")
def get_delivery_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = db.scalar(select(DeliveryProfile).where(DeliveryProfile.user_id == user.id))
    if profile is None:
        profile = DeliveryProfile(user_id=user.id, email=user.email)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return ok(_dump(profile, DeliveryProfileOut))


@router.put("/delivery/profiles/me")
def update_delivery_profile(
    payload: DeliveryProfilePayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = db.scalar(select(DeliveryProfile).where(DeliveryProfile.user_id == user.id))
    if profile is None:
        profile = DeliveryProfile(user_id=user.id)
    _set_fields(profile, payload, ("real_name", "phone", "email", "school", "major", "common_answers"))
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ok(_dump(profile, DeliveryProfileOut), "delivery profile updated")


@router.post("/delivery/tasks")
def create_delivery_task(
    payload: DeliveryTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_job(db, payload.job_id, user.id)
    _validate_resume_reference(db, payload.resume_id, user.id)
    task = DeliveryTask(user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return ok(_dump(task, DeliveryTaskOut), "delivery task created")


@router.post("/delivery/tasks/{task_id}/preview")
def preview_delivery_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _get_delivery_task(db, task_id, user.id)
    job = _get_job(db, task.job_id, user.id)
    profile = db.scalar(select(DeliveryProfile).where(DeliveryProfile.user_id == user.id))
    preview = {
        "site_name": task.site_name or job.company,
        "target_url": task.target_url or job.source_url,
        "fields": {
            "name": profile.real_name if profile else user.username,
            "email": profile.email if profile and profile.email else user.email,
            "phone": profile.phone if profile else "",
            "job": job.title,
        },
    }
    task.preview_data = json.dumps(preview, ensure_ascii=False)
    task.task_status = "previewed"
    db.add(task)
    db.commit()
    db.refresh(task)
    return ok({"task": _dump(task, DeliveryTaskOut), "preview": preview})


@router.post("/delivery/tasks/{task_id}/execute")
def execute_delivery_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _get_delivery_task(db, task_id, user.id)
    if not task.preview_data:
        preview_delivery_task(task_id, db, user)
        task = _get_delivery_task(db, task_id, user.id)
    task.task_status = "success"
    db.add(
        DeliveryTaskLog(
            task_id=task.id,
            user_id=user.id,
            level="info",
            message="已生成字段清单，当前任务未访问真实招聘网站。",
        )
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ok(_dump(task, DeliveryTaskOut), "delivery task executed")


@router.get("/delivery/tasks/{task_id}/logs")
def list_delivery_task_logs(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_delivery_task(db, task_id, user.id)
    logs = db.scalars(
        select(DeliveryTaskLog)
        .where(DeliveryTaskLog.task_id == task_id, DeliveryTaskLog.user_id == user.id)
        .order_by(DeliveryTaskLog.id.desc())
    ).all()
    return ok([_dump(log, DeliveryTaskLogOut) for log in logs])

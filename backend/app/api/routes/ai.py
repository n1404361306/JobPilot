import json
import re

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.routes.business import (
    calculate_match,
    _generate_weekly_report_with_ai,
    _parse_job_with_ai_or_rule,
    _strip_markdown,
)
from app.modules.resume.template_fields import (
    RESUME_TEMPLATE_AI_SYSTEM_PROMPT,
    find_missing_required_placeholders,
)
from app.modules.resume.template_validation import validate_template_content
from app.core.config import get_settings
from app.core.exceptions import BusinessException
from app.core.response import ok
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.models.business import JobSearchReport
from app.models.user import User
from app.modules.ai.client import AIClient
from app.modules.ai.log_service import run_ai_with_log
from app.modules.ai.prompt_service import PromptService
from app.modules.resume.document_extractor import extract_resume_text, save_resume_upload
from app.schemas.business import AIResultOut, AITextRequest, InterviewEvaluateRequest, MatchCalculateRequest, ResumeTemplateChatRequest

from celery.result import AsyncResult
from app.worker.celery_app import celery_app
from app.worker.tasks.ai_tasks import generate_ai_content

router = APIRouter(prefix="/ai", tags=["ai"])


def _result(title: str, content: str, data: dict | None = None) -> dict:
    return AIResultOut(title=title, content=content, data=data or {}).model_dump()


def _prompt_or_default(db: Session, template_code: str, default_prompt: str, variables: dict | None = None) -> str:
    try:
        return PromptService(db).render(template_code, variables or {})
    except Exception:
        return default_prompt


def _provided_resume_fields(source_text: str) -> set[str]:
    labels = {
        "姓名": "姓名",
        "电话": "电话",
        "手机": "电话",
        "邮箱": "邮箱",
        "邮件": "邮箱",
        "GitHub": "GitHub",
        "Github": "GitHub",
        "个人网站": "个人网站",
        "所在地": "所在地",
        "城市": "所在地",
    }
    provided: set[str] = set()
    for label, normalized in labels.items():
        if re.search(rf"{re.escape(label)}\s*[：:]\s*\S+", source_text):
            provided.add(normalized)
    return provided


def _clean_resume_output(content: str, source_text: str = "") -> str:
    provided_fields = _provided_resume_fields(source_text)
    cleaned_lines: list[str] = []
    in_missing_section = False
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue
        if line.startswith("待补充内容"):
            in_missing_section = True
            cleaned_lines.append("待补充内容")
            continue
        if line in {"---", "***", "```"}:
            continue
        if line.startswith(("好的", "根据您的要求", "以下是", "使用说明", "说明：")):
            continue
        line = line.lstrip("#").strip()
        line = line.replace("**", "").replace("__", "").replace("`", "")
        if line.startswith(("- ", "* ", "· ")):
            line = line[2:].strip()
        if in_missing_section and any(field in line for field in provided_fields):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines).strip()
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")
    return cleaned


async def _call_ai(
    db: Session,
    *,
    user_id: int,
    prompt_type: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
) -> str:
    settings = get_settings()
    resolved_system_prompt = _prompt_or_default(
        db,
        prompt_type,
        system_prompt,
        {"user_prompt": user_prompt, "source_text": user_prompt},
    )
    result = await run_ai_with_log(
        db,
        user_id=user_id,
        prompt_type=prompt_type,
        ai_client=AIClient(),
        messages=[
            {"role": "system", "content": resolved_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model_name=settings.ai_primary.model or settings.ai_primary_provider,
        temperature=temperature,
    )
    return result.content.strip()


def _parse_interview_questions(content: str) -> list[str]:
    questions: list[str] = []
    for raw_line in content.splitlines():
        line = _strip_markdown(raw_line.strip())
        line = re.sub(r"^\d+[\.\)、]\s*", "", line).strip()
        if not line or len(line) < 4:
            continue
        if line.startswith(("题目", "面试题", "问题列表", "以下是")):
            continue
        questions.append(line)
    return questions


async def _call_ai_messages_json(
    db: Session,
    *,
    user_id: int,
    prompt_type: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    temperature: float = 0.35,
) -> dict:
    settings = get_settings()
    resolved_system_prompt = _prompt_or_default(db, prompt_type, system_prompt, {})
    result = await run_ai_with_log(
        db,
        user_id=user_id,
        prompt_type=prompt_type,
        ai_client=AIClient(),
        messages=[{"role": "system", "content": resolved_system_prompt}, *messages],
        model_name=settings.ai_primary.model or settings.ai_primary_provider,
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    try:
        return json.loads(result.content)
    except json.JSONDecodeError:
        return {"raw_content": result.content}


def _unwrap_template_code_fence(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[\w-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


async def _call_ai_json(
    db: Session,
    *,
    user_id: int,
    prompt_type: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
) -> dict:
    settings = get_settings()
    resolved_system_prompt = _prompt_or_default(
        db,
        prompt_type,
        system_prompt,
        {"user_prompt": user_prompt, "source_text": user_prompt},
    )
    result = await run_ai_with_log(
        db,
        user_id=user_id,
        prompt_type=prompt_type,
        ai_client=AIClient(),
        messages=[
            {"role": "system", "content": resolved_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model_name=settings.ai_primary.model or settings.ai_primary_provider,
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    try:
        return json.loads(result.content)
    except json.JSONDecodeError:
        return {"raw_content": result.content}


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _resume_data_to_text(data: dict) -> str:
    basic = data.get("basic_info") or {}
    skills = data.get("skills") or {}
    lines = [
        "基本信息",
        f"姓名：{basic.get('name') or ''}",
        f"电话：{basic.get('phone') or ''}",
        f"邮箱：{basic.get('email') or ''}",
        f"GitHub：{basic.get('github') or ''}",
        f"个人网站：{basic.get('website') or ''}",
        f"所在地：{basic.get('location') or ''}",
        "",
        "个人简介",
        data.get("summary") or "暂无明确内容",
        "",
        "求职意向",
        data.get("job_intention") or "暂无明确内容",
        "",
        "专业技能",
    ]
    for label, key in [
        ("编程语言", "languages"),
        ("后端开发", "backend"),
        ("数据库与中间件", "database"),
        ("AI / 算法", "ai"),
        ("工程工具", "tools"),
        ("语言能力", "language_ability"),
    ]:
        values = _as_list(skills.get(key))
        lines.append(f"{label}：{'、'.join(str(item) for item in values) if values else '暂无明确内容'}")

    def add_items(title: str, items: list, fields: list[tuple[str, str]]) -> None:
        lines.extend(["", title])
        if not items:
            lines.append("暂无明确内容")
            return
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                lines.append(f"{index}. {item}")
                continue
            heading_parts = [str(item.get(key) or "") for key in ("name", "organization", "company", "school", "project_name", "title")]
            heading = next((part for part in heading_parts if part), title)
            lines.append(f"{index}. {heading}")
            for label, key in fields:
                value = item.get(key)
                if isinstance(value, list):
                    value = "；".join(str(v) for v in value)
                lines.append(f"   {label}：{value or '暂无明确内容'}")

    add_items("教育经历", _as_list(data.get("education")), [
        ("学校", "school"), ("专业", "major"), ("学历", "degree"), ("时间", "period"),
        ("研究方向", "research_direction"), ("GPA", "gpa"), ("课程/荣誉", "highlights"),
    ])
    add_items("实习经历", _as_list(data.get("internships")), [
        ("公司", "company"), ("职位", "position"), ("时间", "period"), ("地点", "location"),
        ("工作概述", "description"), ("主要工作", "responsibilities"), ("技术栈", "tech_stack"),
    ])
    add_items("项目经历", _as_list(data.get("projects")), [
        ("项目类型", "type"), ("时间", "period"), ("项目概述", "description"),
        ("主要职责", "responsibilities"), ("技术栈", "tech_stack"), ("项目成果", "results"),
    ])
    add_items("科研经历", _as_list(data.get("research")), [
        ("研究主题", "title"), ("时间", "period"), ("研究内容", "content"),
    ])

    lines.extend(["", "获奖证书"])
    awards = _as_list(data.get("awards"))
    certificates = _as_list(data.get("certificates"))
    lines.append(f"获奖经历：{'；'.join(str(item) for item in awards) if awards else '暂无明确内容'}")
    lines.append(f"证书：{'、'.join(str(item) for item in certificates) if certificates else '暂无明确内容'}")
    lines.append(f"开源贡献：{data.get('open_source') or '暂无明确内容'}")
    lines.append(f"兴趣方向：{data.get('interests') or '暂无明确内容'}")

    missing = _as_list(data.get("missing_items"))
    lines.extend(["", "待补充内容"])
    if missing:
        lines.extend(f"{index}. {item}" for index, item in enumerate(missing, start=1))
    else:
        lines.append("暂无")
    return "\n".join(lines).strip()


RESUME_JSON_SCHEMA = (
    "{\n"
    '  "basic_info": {"name":"", "phone":"", "email":"", "github":"", "website":"", "location":""},\n'
    '  "job_intention": "",\n'
    '  "summary": "",\n'
    '  "skills": {"languages":[], "backend":[], "database":[], "ai":[], "tools":[], "language_ability":[]},\n'
    '  "education": [{"school":"", "major":"", "degree":"", "period":"", "research_direction":"", "gpa":"", "highlights":[]}],\n'
    '  "internships": [{"company":"", "position":"", "period":"", "location":"", "description":"", "responsibilities":[], "tech_stack":[]}],\n'
    '  "projects": [{"project_name":"", "type":"", "period":"", "description":"", "responsibilities":[], "tech_stack":[], "results":[]}],\n'
    '  "research": [{"title":"", "period":"", "content":[]}],\n'
    '  "awards": [],\n'
    '  "certificates": [],\n'
    '  "open_source": "",\n'
    '  "interests": "",\n'
    '  "self_evaluation": "",\n'
    '  "missing_items": []\n'
    "}"
)

RESUME_JSON_SYSTEM_PROMPT = (
    "你是简历信息抽取助手。请把用户输入解析为严格 JSON 对象，供前端表单编辑。"
    "只能使用用户明确提供的信息，严禁编造。未提供的字段用空字符串、空数组或放入 missing_items。"
    "必须返回合法 JSON，不要 Markdown，不要解释。"
    "若文本来自 OCR，请修正明显错字，无法确认的信息放入 missing_items 并标注需人工确认。"
)


def _resume_json_user_prompt(source_text: str) -> str:
    return (
        f"请按这个 JSON 结构输出：\n{RESUME_JSON_SCHEMA}\n"
        "要求：姓名、电话、邮箱、GitHub、个人网站、所在地如果已给出，必须放入 basic_info，不能放入 missing_items。"
        "summary 可根据个人评价、技能、实习和项目概括 2 到 4 句。数组字段请保留多条经历，不要压缩成一个字符串。\n\n"
        f"简历内容：\n{source_text}"
    )


async def _parse_resume_to_form(
    db: Session,
    *,
    user_id: int,
    source_text: str,
    prompt_type: str,
    extra_data: dict | None = None,
) -> dict:
    if not source_text.strip():
        raise BusinessException(code=4008, message="resume content is empty")

    data = await _call_ai_json(
        db,
        user_id=user_id,
        prompt_type=prompt_type,
        system_prompt=RESUME_JSON_SYSTEM_PROMPT,
        user_prompt=_resume_json_user_prompt(source_text),
        temperature=0.1,
    )
    content = _resume_data_to_text(data)
    payload = {"content": content, "resume_form": data, "source_text": source_text}
    if extra_data:
        payload.update(extra_data)
    return ok(_result("结构化简历草稿", content, payload))


@router.post("/resumes/generate-from-text")
async def generate_resume_from_text(
    payload: AITextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _parse_resume_to_form(
        db,
        user_id=user.id,
        source_text=payload.text,
        prompt_type="resume_generate",
    )


@router.post("/resumes/parse-file")
async def parse_resume_file(
    payload: AITextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _parse_resume_to_form(
        db,
        user_id=user.id,
        source_text=payload.text,
        prompt_type="resume_parse",
    )


@router.post("/resumes/parse-upload")
async def parse_resume_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_path, file_name, _file_type, _file_size = await save_resume_upload(user_id=user.id, upload=file)
    try:
        extracted_text, source_type, engine = extract_resume_text(file_path)
    except BusinessException:
        raise
    except Exception as exc:
        raise BusinessException(code=5005, message=f"文件解析失败：{exc}") from exc

    if not extracted_text.strip():
        raise BusinessException(code=4008, message="未能从文件中提取到有效文字")

    return await _parse_resume_to_form(
        db,
        user_id=user.id,
        source_text=extracted_text,
        prompt_type="resume_parse_upload",
        extra_data={
            "file_name": file_name,
            "source_type": source_type,
            "extract_engine": engine,
        },
    )


@router.post("/resumes/parse-ocr-text")
async def parse_resume_ocr_text(
    payload: AITextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _parse_resume_to_form(
        db,
        user_id=user.id,
        source_text=payload.text,
        prompt_type="resume_parse_ocr",
        extra_data={"source_type": "ocr-text"},
    )
    content = await _call_ai(
        db,
        user_id=user.id,
        prompt_type="resume_parse_ocr",
        system_prompt=(
            "你是 OCR 简历纠错和结构化助手。请修正明显 OCR 错字，并把内容整理为可编辑简历。"
            "无法确认的信息请标注“需人工确认”。"
        ),
        user_prompt=f"OCR 文本如下：\n{payload.text}",
    )
    return ok(_result("OCR 结构化简历", content, {"content": content}))


@router.post("/jobs/parse")
async def parse_job(
    payload: AITextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job_form = await _parse_job_with_ai_or_rule(db, user.id, payload.text)
    content = "\n".join(
        [
            f"岗位名称：{job_form.get('title') or ''}",
            f"公司：{job_form.get('company') or ''}",
            f"地点：{job_form.get('location') or ''}",
            f"薪资：{job_form.get('salary_range') or ''}",
            f"截止时间：{job_form.get('deadline') or ''}",
            f"标签：{job_form.get('tags') or ''}",
            "",
            str(job_form.get("description") or ""),
        ]
    ).strip()
    return ok(_result("结构化岗位解析结果", content, {"source_text": payload.text, "job_form": job_form}))
    content = await _call_ai(
        db,
        user_id=user.id,
        prompt_type="job_parse",
        system_prompt="你是岗位 JD 解析助手。请提取岗位名称、公司、地点、职责、要求、技能关键词、投递方式和风险提示。",
        user_prompt=f"请解析以下岗位信息：\n{payload.text}",
    )
    return ok(_result("岗位解析结果", content, {"source_text": payload.text}))


@router.post("/matching/analyze")
async def analyze_matching(
    payload: MatchCalculateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await calculate_match(payload, db, user)


@router.post("/resumes/optimize")
async def optimize_resume(
    payload: AITextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await _call_ai(
        db,
        user_id=user.id,
        prompt_type="resume_optimize",
        system_prompt=(
            "你是中文简历优化专家。请给出具体、可执行的优化建议。"
            "重点关注表达清晰度、量化成果、关键词覆盖、项目经历可信度和风险项。"
            "使用纯中文段落输出，不要使用 markdown 符号（如 # * ** -）。"
        ),
        user_prompt=f"请优化以下简历/岗位材料：\n{payload.text}",
    )
    return ok(_result("简历优化建议", _strip_markdown(content)))


@router.post("/resumes/adapt-to-job")
async def adapt_resume_to_job(
    payload: AITextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await _call_ai(
        db,
        user_id=user.id,
        prompt_type="resume_adapt",
        system_prompt=(
            "你是岗位适配简历顾问。请基于用户已有经历，生成针对目标岗位的适配建议和改写片段。"
            "严禁编造不存在的经历。使用纯中文段落输出，不要使用 markdown 符号（如 # * ** -）。"
        ),
        user_prompt=f"请根据以下简历与岗位信息生成适配建议：\n{payload.text}",
    )
    return ok(_result("岗位适配建议", _strip_markdown(content)))


@router.post("/interviews/questions")
async def generate_interview_questions(
    payload: AITextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await _call_ai(
        db,
        user_id=user.id,
        prompt_type="interview_questions",
        system_prompt=(
            "你是面试官。请基于候选人背景和岗位方向生成 8 道中文模拟面试题，覆盖项目、技术、行为和反问。"
            "每题单独一行，以数字序号开头。不要使用 markdown 符号（如 # * ** -）。"
        ),
        user_prompt=f"面试背景：\n{payload.text}",
    )
    questions = _parse_interview_questions(content)
    return ok(_result("模拟面试题", _strip_markdown(content), {"questions": questions}))


@router.post("/interviews/evaluate-answer")
async def evaluate_interview_answer(
    payload: InterviewEvaluateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await _call_ai(
        db,
        user_id=user.id,
        prompt_type="interview_evaluate",
        system_prompt=(
            "你是面试评价助手。请对回答给出 100 分制评分、优点、不足、追问建议和一版更好的参考回答。"
            "评价要具体，不要空泛。使用纯中文段落输出，不要使用 markdown 符号（如 # * ** -）。"
        ),
        user_prompt=f"题目：{payload.question}\n\n候选人回答：\n{payload.answer}",
    )
    return ok(_result("面试回答评价", _strip_markdown(content)))


@router.post("/resume-templates/chat")
async def chat_resume_template(
    payload: ResumeTemplateChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    messages: list[dict[str, str]] = []
    for item in payload.history:
        messages.append({"role": item.role, "content": item.content})

    user_parts = [payload.message.strip()]
    if payload.current_template and payload.current_template.strip():
        user_parts.append(f"当前模板 HTML：\n{payload.current_template.strip()}")
    messages.append({"role": "user", "content": "\n\n".join(user_parts)})

    data = await _call_ai_messages_json(
        db,
        user_id=user.id,
        prompt_type="resume_template_design",
        system_prompt=RESUME_TEMPLATE_AI_SYSTEM_PROMPT,
        messages=messages,
        temperature=0.35,
    )

    summary = str(data.get("summary") or data.get("message") or "模板已生成，请在右侧预览效果。").strip()
    template_content = _unwrap_template_code_fence(
        str(data.get("template_content") or data.get("content") or data.get("raw_content") or "")
    )
    if not template_content:
        raise BusinessException(code=5002, message="AI 未返回有效模板内容")

    try:
        template_content = validate_template_content(template_content)
    except ValueError as exc:
        raise BusinessException(code=4006, message=str(exc)) from exc

    missing_fields = find_missing_required_placeholders(template_content)
    if missing_fields:
        summary = f"{summary}\n\n注意：模板仍缺少字段占位符：{', '.join(missing_fields)}。请在下一轮要求 AI 补全。"

    return ok(
        _result(
            "AI 简历模板",
            summary,
            {
                "template_content": template_content,
                "summary": summary,
                "missing_fields": missing_fields,
            },
        )
    )


@router.post("/reports/weekly")
async def generate_weekly_report(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await _generate_weekly_report_with_ai(db, user)
    report = JobSearchReport(user_id=user.id, title="AI 求职周报", content=content, report_type="weekly")
    db.add(report)
    db.commit()
    db.refresh(report)
    return ok(
        {
            "id": report.id,
            "user_id": report.user_id,
            "title": report.title,
            "content": report.content,
            "report_type": report.report_type,
            "created_at": report.created_at,
        },
        "weekly report created",
    )

    # content = await _call_ai(
    #     db,
    #     user_id=user.id,
    #     prompt_type="weekly_report",
    #     system_prompt="你是求职复盘顾问。请生成一份中文求职周报，包含进展、问题、下周计划和提醒。",
    #     user_prompt="请基于当前系统中的求职数据生成一份简洁周报；如果数据不足，请给出下一步建议。",
    # )
    # report = JobSearchReport(user_id=user.id, title="AI 求职周报", content=content, report_type="weekly")
    # db.add(report)
    # db.commit()
    # db.refresh(report)
    # return ok(
    #     {
    #         "id": report.id,
    #         "user_id": report.user_id,
    #         "title": report.title,
    #         "content": report.content,
    #         "report_type": report.report_type,
    #         "created_at": report.created_at,
    #     },
    #     "weekly report created",
    # )

@router.post("/resumes/optimize-async")
async def optimize_resume_async(
    payload: AITextRequest,
    user: User = Depends(get_current_user),
):
    async_result = generate_ai_content.delay(
        user_id=user.id,
        prompt_type="resume_optimize",
        system_prompt="你是中文简历优化专家。...",
        user_prompt=f"请优化以下简历/岗位材料：\n{payload.text}",
    )
    return ok({"task_status": "pending", "worker_task_id": async_result.id})
    
@router.get("/tasks/{worker_task_id}")
def get_ai_worker_task(worker_task_id: str, user: User = Depends(get_current_user)):
    _ = user
    result = AsyncResult(worker_task_id, app=celery_app)
    if not result.ready():
        return ok({"task_status": "running"})
    payload = result.get(propagate=False)
    if payload.get("status") == "success":
        return ok(_result("简历优化建议", _strip_markdown(payload["content"])))
    return ok({"task_status": "failed", "error": payload.get("error")})

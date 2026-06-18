"""
D3.16 JobParseService 单元测试

运行：
    cd /root/JobPilot/backend
    python -m pytest test/test_job_parse_service.py -v
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import BusinessException
from app.models.file_resource import FileResource
from app.models.ocr_task import OCRTask
from app.modules.ai.prompt_constants import PROMPT_TYPE_JOB_PARSE
from app.modules.ai.schemas import AIChatResult, AIUsage
from app.modules.ocr.ocr_constants import OCR_TASK_FAILED, OCR_TASK_SUCCESS
from app.schemas.ai import ParseJobRequest

# 与当前文件名一致（注意 parsse 拼写）
from app.modules.ai.job_parsse_service import JobParseService


SAMPLE_JD_TEXT = """
【公司名称】云途科技有限公司
【岗位名称】Python 后端开发工程师
【工作城市】上海
【岗位类型】全职
【薪资范围】15K-25K
【截止日期】2026-07-31
岗位职责：
1. 负责后端 API 设计与开发，维护核心业务服务。
2. 参与数据库设计与性能优化。
任职要求：
1. 本科及以上学历，计算机相关专业。
2. 熟悉 Python、FastAPI/Flask、MySQL。
关键词：Python、FastAPI、MySQL、Redis、后端开发
""".strip()


FAKE_PARSED_JOB = {
    "company_name": "云途科技有限公司",
    "job_title": "Python 后端开发工程师",
    "city": "上海",
    "job_type": "全职",
    "salary_range": "15K-25K",
    "deadline": "2026-07-31",
    "source_url": "",
    "responsibility_summary": "负责后端 API 设计与开发",
    "requirement_summary": "熟悉 Python、FastAPI、MySQL",
    "education_required": "本科及以上",
    "experience_required": "有项目或实习经验",
    "skill_keywords": ["Python", "FastAPI", "MySQL", "Redis"],
    "tags": ["后端开发"],
}


def make_ai_result(content: dict | str) -> AIChatResult:
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False)
    return AIChatResult(
        content=content,
        usage=AIUsage(
            provider="mock",
            model="mock-model",
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
            duration_ms=100,
        ),
        provider="mock",
        model="mock-model",
    )


@pytest.fixture
def sample_job_file(db, tmp_path):
    image_path = tmp_path / "job_screenshot.png"
    image_path.write_bytes(b"fake-job-screenshot")

    record = FileResource(
        user_id=1,
        file_name="job_screenshot.png",
        file_path=str(image_path),
        file_type="image/png",
        file_size=20,
        related_type="ocr",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.fixture
def ocr_task_success(db, sample_job_file):
    task = OCRTask(
        user_id=1,
        file_id=sample_job_file.id,
        task_status=OCR_TASK_SUCCESS,
        page_count=1,
        ocr_text=SAMPLE_JD_TEXT,
        confidence_avg=Decimal("0.91"),
        created_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def ocr_task_pending(db, sample_job_file):
    task = OCRTask(
        user_id=1,
        file_id=sample_job_file.id,
        task_status="pending",
        page_count=0,
        ocr_text=None,
        created_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def ocr_task_empty_text(db, sample_job_file):
    task = OCRTask(
        user_id=1,
        file_id=sample_job_file.id,
        task_status=OCR_TASK_SUCCESS,
        page_count=1,
        ocr_text="   ",
        confidence_avg=Decimal("0.50"),
        created_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# ---------- D3.1 成功：raw_jd 文本解析 ----------

@pytest.mark.asyncio
async def test_parse_job_from_raw_jd_success(db):
    service = JobParseService(db)

    with patch(
        "app.modules.ai.job_parsse_service.run_ai_with_log",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = make_ai_result(FAKE_PARSED_JOB)
        result = await service.parse_job(user_id=1, raw_jd=SAMPLE_JD_TEXT)

    assert result.prompt_type == PROMPT_TYPE_JOB_PARSE
    assert result.source_type == "text"
    assert result.task_id is None
    assert result.parsed.company_name == "云途科技有限公司"
    assert result.parsed.job_title == "Python 后端开发工程师"
    assert "Python" in result.parsed.skill_keywords

    mock_run.assert_awaited_once()
    call_kwargs = mock_run.await_args.kwargs
    assert call_kwargs["prompt_type"] == PROMPT_TYPE_JOB_PARSE
    assert call_kwargs["user_id"] == 1
    assert call_kwargs["response_format"] == {"type": "json_object"}


# ---------- D3.2 成功：task_id（OCR 任务）解析 ----------

@pytest.mark.asyncio
async def test_parse_job_from_task_id_success(db, ocr_task_success):
    service = JobParseService(db)

    with patch(
        "app.modules.ai.job_parsse_service.run_ai_with_log",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = make_ai_result(FAKE_PARSED_JOB)
        result = await service.parse_job(user_id=1, task_id=ocr_task_success.id)

    assert result.source_type == "ocr"
    assert result.task_id == ocr_task_success.id
    assert result.parsed.job_title == "Python 后端开发工程师"


# ---------- D3.3 source_url 回填 ----------

@pytest.mark.asyncio
async def test_parse_job_fills_source_url_when_llm_empty(db):
    service = JobParseService(db)
    payload = dict(FAKE_PARSED_JOB)
    payload["source_url"] = ""

    with patch(
        "app.modules.ai.job_parsse_service.run_ai_with_log",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = make_ai_result(payload)
        result = await service.parse_job(
            user_id=1,
            raw_jd=SAMPLE_JD_TEXT,
            source_url="https://example.com/job/123",
        )

    assert result.parsed.source_url == "https://example.com/job/123"


# ---------- D3.4 失败：OCR 任务未完成 ----------

@pytest.mark.asyncio
async def test_parse_job_task_not_completed(db, ocr_task_pending):
    service = JobParseService(db)

    with pytest.raises(BusinessException) as exc:
        await service.parse_job(user_id=1, task_id=ocr_task_pending.id)

    assert exc.value.code == 4007
    assert "not completed" in exc.value.message


# ---------- D3.5 失败：OCR 文本为空 ----------

@pytest.mark.asyncio
async def test_parse_job_empty_ocr_text(db, ocr_task_empty_text):
    service = JobParseService(db)

    with pytest.raises(BusinessException) as exc:
        await service.parse_job(user_id=1, task_id=ocr_task_empty_text.id)

    assert exc.value.code == 4008
    assert "empty" in exc.value.message.lower()


# ---------- D3.6 失败：raw_jd 为空 ----------

@pytest.mark.asyncio
async def test_parse_job_empty_raw_jd(db):
    service = JobParseService(db)

    with pytest.raises(BusinessException) as exc:
        await service.parse_job(user_id=1, raw_jd="   ")

    assert exc.value.code == 4008


# ---------- D3.7 失败：LLM 返回非法 JSON ----------

@pytest.mark.asyncio
async def test_parse_job_invalid_llm_json(db):
    service = JobParseService(db)

    with patch(
        "app.modules.ai.job_parsse_service.run_ai_with_log",
        new_callable=AsyncMock,
    ) as mock_run:
        mock_run.return_value = make_ai_result("not-json")
        with pytest.raises(BusinessException) as exc:
            await service.parse_job(user_id=1, raw_jd=SAMPLE_JD_TEXT)

    assert exc.value.code == 5002
    assert "invalid JSON" in exc.value.message


# ---------- D3.8 失败：task 不属于当前用户 ----------

@pytest.mark.asyncio
async def test_parse_job_task_not_owned_by_user(db, ocr_task_success):
    service = JobParseService(db)

    with pytest.raises(BusinessException) as exc:
        await service.parse_job(user_id=999, task_id=ocr_task_success.id)

    assert exc.value.code == 4045
    assert "ocr task not found" in exc.value.message


# ---------- D3.9 失败：task_id 不存在 ----------

@pytest.mark.asyncio
async def test_parse_job_task_not_found(db):
    service = JobParseService(db)

    with pytest.raises(BusinessException) as exc:
        await service.parse_job(user_id=1, task_id=999999)

    assert exc.value.code == 4045


# ---------- D3.10 Schema：ParseJobRequest 校验 ----------

def test_parse_job_request_accepts_task_id_only():
    req = ParseJobRequest(task_id=1)
    assert req.task_id == 1


def test_parse_job_request_accepts_raw_jd_only():
    req = ParseJobRequest(raw_jd=SAMPLE_JD_TEXT)
    assert req.raw_jd == SAMPLE_JD_TEXT


def test_parse_job_request_rejects_all_missing():
    with pytest.raises(ValueError):
        ParseJobRequest()


def test_parse_job_request_accepts_source_url_only():
    # 当前 schema 允许仅 source_url；service 层仍会因 JD 为空失败
    req = ParseJobRequest(source_url="https://example.com/job/1")
    assert req.source_url == "https://example.com/job/1"
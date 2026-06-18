from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ApplicationStatus = Literal[
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
]
JobStatus = Literal["active", "closed", "archived"]


class ResumeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1)
    file_url: str | None = Field(default=None, max_length=512)
    is_default: bool = False


class ResumeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    content: str | None = Field(default=None, min_length=1)
    file_url: str | None = Field(default=None, max_length=512)
    is_default: bool | None = None


class ResumeOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    file_url: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class ResumeTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)
    content: str = Field(min_length=1)
    enabled: bool = True
    is_system: bool = False
    is_public: bool = False


class ResumeTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None
    is_public: bool | None = None


class ResumeTemplateOut(BaseModel):
    id: int
    user_id: int | None = None
    name: str
    description: str | None
    content: str
    enabled: bool
    is_system: bool = True
    is_public: bool = False
    copied_from_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ResumeTemplateSelectRequest(BaseModel):
    template_id: str = Field(min_length=1, max_length=64)


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    company: str = Field(min_length=1, max_length=128)
    location: str | None = Field(default=None, max_length=128)
    salary_range: str | None = Field(default=None, max_length=128)
    source_url: str | None = Field(default=None, max_length=512)
    source_type: str | None = Field(default=None, max_length=64)
    job_type: str | None = Field(default=None, max_length=64)
    deadline: str | None = Field(default=None, max_length=64)
    tags: str | None = Field(default=None, max_length=512)
    is_favorite: bool = False
    import_batch_id: str | None = Field(default=None, max_length=64)
    description: str | None = None
    status: JobStatus = "active"


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    company: str | None = Field(default=None, min_length=1, max_length=128)
    location: str | None = Field(default=None, max_length=128)
    salary_range: str | None = Field(default=None, max_length=128)
    source_url: str | None = Field(default=None, max_length=512)
    source_type: str | None = Field(default=None, max_length=64)
    job_type: str | None = Field(default=None, max_length=64)
    deadline: str | None = Field(default=None, max_length=64)
    tags: str | None = Field(default=None, max_length=512)
    is_favorite: bool | None = None
    import_batch_id: str | None = Field(default=None, max_length=64)
    description: str | None = None
    status: JobStatus | None = None


class JobOut(BaseModel):
    id: int
    user_id: int
    title: str
    company: str
    location: str | None
    salary_range: str | None
    source_url: str | None
    source_type: str | None = None
    job_type: str | None = None
    deadline: str | None = None
    tags: str | None = None
    is_favorite: bool = False
    import_batch_id: str | None = None
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: int | None = None
    status: ApplicationStatus = "pending"
    channel: str | None = Field(default=None, max_length=64)
    note: str | None = None
    applied_at: datetime | None = None


class ApplicationUpdate(BaseModel):
    resume_id: int | None = None
    status: ApplicationStatus | None = None
    channel: str | None = Field(default=None, max_length=64)
    note: str | None = None
    applied_at: datetime | None = None


class ApplicationOut(BaseModel):
    id: int
    user_id: int
    job_id: int
    resume_id: int | None
    status: str
    channel: str | None
    note: str | None
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ResumeVersionCreate(BaseModel):
    version_name: str = Field(default="初始版本", min_length=1, max_length=128)
    content: str = Field(min_length=1)
    structured_data: str | None = None


class ResumeVersionUpdate(BaseModel):
    version_name: str | None = Field(default=None, min_length=1, max_length=128)
    content: str | None = Field(default=None, min_length=1)
    structured_data: str | None = None


class ResumeVersionOut(BaseModel):
    id: int
    resume_id: int
    user_id: int
    version_name: str
    content: str
    structured_data: str | None
    created_at: datetime
    updated_at: datetime


class ResumeRenderRequest(BaseModel):
    template_id: int | None = None


class JobImportTextRequest(BaseModel):
    text: str = Field(min_length=1)
    source_url: str | None = Field(default=None, max_length=512)


class JobImportUrlRequest(BaseModel):
    source_url: str = Field(min_length=1, max_length=512)
    text: str | None = None


class JobBatchImportRequest(BaseModel):
    text: str = Field(min_length=1)
    separator: str | None = None


class JobBatchConfirmRequest(BaseModel):
    jobs: list[JobCreate] = Field(min_length=1)


class MatchCalculateRequest(BaseModel):
    resume_id: int
    job_id: int


class MatchReportOut(BaseModel):
    id: int
    user_id: int
    resume_id: int
    job_id: int
    score: int
    summary: str
    strengths: str | None
    gaps: str | None
    suggestions: str | None
    created_at: datetime


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: str | None = None


class ApplicationStatusHistoryOut(BaseModel):
    id: int
    application_id: int
    user_id: int
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime


class ReportOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    report_type: str
    created_at: datetime


class DeliveryProfilePayload(BaseModel):
    real_name: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    school: str | None = Field(default=None, max_length=128)
    major: str | None = Field(default=None, max_length=128)
    common_answers: str | None = None


class DeliveryProfileOut(DeliveryProfilePayload):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class DeliveryTaskCreate(BaseModel):
    job_id: int
    resume_id: int | None = None
    site_name: str | None = Field(default=None, max_length=128)
    target_url: str | None = Field(default=None, max_length=512)


class DeliveryTaskOut(BaseModel):
    id: int
    user_id: int
    job_id: int
    resume_id: int | None
    site_name: str | None
    target_url: str | None
    task_status: str
    preview_data: str | None
    created_at: datetime
    updated_at: datetime


class DeliveryTaskLogOut(BaseModel):
    id: int
    task_id: int
    user_id: int
    level: str
    message: str
    created_at: datetime


class AITextRequest(BaseModel):
    text: str = Field(min_length=1)
    resume_id: int | None = None
    job_id: int | None = None


class InterviewEvaluateRequest(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    resume_id: int | None = None
    job_id: int | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ResumeTemplateChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    current_template: str | None = None


class AIResultOut(BaseModel):
    title: str
    content: str
    data: dict[str, Any] | None = None

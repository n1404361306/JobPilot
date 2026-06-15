from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ApplicationStatus = Literal["pending", "submitted", "interview", "offer", "rejected", "withdrawn"]
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


class ResumeTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None


class ResumeTemplateOut(BaseModel):
    id: int
    name: str
    description: str | None
    content: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    company: str = Field(min_length=1, max_length=128)
    location: str | None = Field(default=None, max_length=128)
    salary_range: str | None = Field(default=None, max_length=128)
    source_url: str | None = Field(default=None, max_length=512)
    description: str | None = None
    status: JobStatus = "active"


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    company: str | None = Field(default=None, min_length=1, max_length=128)
    location: str | None = Field(default=None, max_length=128)
    salary_range: str | None = Field(default=None, max_length=128)
    source_url: str | None = Field(default=None, max_length=512)
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

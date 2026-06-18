from pydantic import BaseModel, Field, model_validator

class ParseOcrTextRequest(BaseModel):
    task_id: int | None = None
    ocr_text: str | None = None

    @model_validator(mode="after")
    def check_one_of(self):
        has_task = self.task_id is not None
        has_text = bool((self.ocr_text or "").strip())
        if has_task == has_text:
            raise ValueError("either task_id or ocr_text must be provided")
        return self
    
class ResumeBasicInfo(BaseModel):
    real_name: str = ""
    phone: str = ""
    email: str = ""
    city: str = ""

class ParsedResumeContent(BaseModel):
    title: str = ""
    target_position: str = ""
    summary: str = ""
    basic_info: ResumeBasicInfo = Field(default_factory=ResumeBasicInfo)
    education_list: list[dict] = Field(default_factory=list)
    project_list: list[dict] = Field(default_factory=list)
    internship_list: list[dict] = Field(default_factory=list)
    skill_list: list[dict] = Field(default_factory=list)
    award_list: list[dict] = Field(default_factory=list)

class ParseOcrTextOut(BaseModel):
    task_id: int | None = None
    source_type: str = "ocr"
    prompt_type: str
    parsed: ParsedResumeContent


class ParseJobRequest(BaseModel):
    task_id: int | None = None
    raw_jd: str | None = None
    source_url: str | None = None

    @model_validator(mode="after")
    def check_one_of(self):
        has_task = self.task_id is not None
        has_jd = bool((self.raw_jd or "").strip())
        has_url = bool((self.source_url or "").strip())
        if has_task == has_jd == has_url:
            raise ValueError("either task_id or raw_jd or source_url must be provided")
        return self

class ParseJobContent(BaseModel):
    company_name: str = ""
    job_title: str = ""
    city: str = ""
    job_type: str = ""
    salary_range: str = ""
    deadline: str = ""
    source_url: str = ""
    responsibility_summary: str = ""
    requirement_summary: str = ""
    education_required: str = ""
    experience_required: str = ""
    skill_keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

class ParseJobOut(BaseModel):
    task_id: int | None = None
    source_type: str = "ocr" ## ocr or text
    prompt_type: str
    parsed: ParseJobContent



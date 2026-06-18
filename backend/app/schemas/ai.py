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


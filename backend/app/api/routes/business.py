from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.response import ok
from app.db.session import get_db
from app.deps.auth import get_current_user, require_permissions
from app.models.business import Application, Job, Resume, ResumeTemplate
from app.models.user import User
from app.schemas.business import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    JobCreate,
    JobOut,
    JobUpdate,
    ResumeCreate,
    ResumeOut,
    ResumeTemplateCreate,
    ResumeTemplateOut,
    ResumeTemplateUpdate,
    ResumeUpdate,
)

router = APIRouter(tags=["business"])


def _dump(model, schema):
    return schema.model_validate(model, from_attributes=True).model_dump()


def _set_fields(model, payload, fields: tuple[str, ...]) -> None:
    data = payload.model_dump(exclude_unset=True)
    for field in fields:
        if field in data:
            setattr(model, field, data[field])


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


@router.get("/resume-templates")
def list_resume_templates(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    templates = db.scalars(
        select(ResumeTemplate).where(ResumeTemplate.enabled.is_(True)).order_by(ResumeTemplate.id.desc())
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
    template = ResumeTemplate(**payload.model_dump())
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
    _set_fields(template, payload, ("name", "description", "content", "enabled"))
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


@router.get("/jobs")
def list_jobs(
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Job).where(Job.user_id == user.id)
    if status:
        stmt = stmt.where(Job.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where((Job.title.like(pattern)) | (Job.company.like(pattern)))
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
    return ok(_dump(application, ApplicationOut), "application created")


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
    for field, value in data.items():
        setattr(application, field, value)
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

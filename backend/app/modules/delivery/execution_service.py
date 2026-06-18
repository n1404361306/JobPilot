import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.business import DeliveryProfile, DeliveryTask, DeliveryTaskLog, Job
from app.models.user import User


class DeliveryExecutionService:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, *, task_id: int, user_id: int) -> DeliveryTask:
        task = self._get_task(task_id, user_id)
        user = self.db.get(User, user_id)
        if user is None:
            raise BusinessException(code=4040, message="user not found")

        if not task.preview_data:
            self._build_preview(task, user)

        task.task_status = "running"
        self._add_log(task, user_id, "Worker 开始执行投递任务")

        # 第一阶段：模拟执行（Playwright 下一步再加）
        task.task_status = "success"
        self._add_log(
            task,
            user_id,
            "已生成字段清单，当前任务未访问真实招聘网站。",
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def _build_preview(self, task: DeliveryTask, user: User) -> None:
        job = self._get_job(task.job_id, user.id)
        profile = self.db.scalar(select(DeliveryProfile).where(DeliveryProfile.user_id == user.id))
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
        self.db.add(task)
        self.db.commit()

    def _add_log(self, task: DeliveryTask, user_id: int, message: str) -> None:
        self.db.add(
            DeliveryTaskLog(
                task_id=task.id,
                user_id=user_id,
                level="info",
                message=message,
            )
        )

    def _get_task(self, task_id: int, user_id: int) -> DeliveryTask:
        task = self.db.scalar(
            select(DeliveryTask).where(DeliveryTask.id == task_id, DeliveryTask.user_id == user_id)
        )
        if not task:
            raise BusinessException(code=4048, message="delivery task not found")
        return task

    def _get_job(self, job_id: int, user_id: int) -> Job:
        job = self.db.scalar(select(Job).where(Job.id == job_id, Job.user_id == user_id))
        if not job:
            raise BusinessException(code=4047, message="job not found")
        return job
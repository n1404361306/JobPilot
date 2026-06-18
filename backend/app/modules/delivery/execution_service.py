import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.business import DeliveryProfile, DeliveryTask, DeliveryTaskLog, Job
from app.models.user import User


class DeliveryExecutionService:
    def __init__(self, db: Session):
        self.db = db

    # def execute(self, *, task_id: int, user_id: int) -> DeliveryTask:
    #     task = self._get_task(task_id, user_id)
    #     user = self.db.get(User, user_id)
    #     if user is None:
    #         raise BusinessException(code=4040, message="user not found")

    #     if not task.preview_data:
    #         self._build_preview(task, user)

    #     task.task_status = "running"
    #     self._add_log(task, user_id, "Worker 开始执行投递任务")

    #     # 第一阶段：模拟执行（Playwright 下一步再加）
    #     task.task_status = "success"
    #     self._add_log(
    #         task,
    #         user_id,
    #         "已生成字段清单，当前任务未访问真实招聘网站。",
    #     )
    #     self.db.add(task)
    #     self.db.commit()
    #     self.db.refresh(task)
    #     return task

    def execute(self, *, task_id: int, user_id: int) -> DeliveryTask:
        task = self._get_task(task_id, user_id)
        user = self._require_user(user_id)

        # Step 1: 确保 preview
        if not task.preview_data:
            self._build_preview(task, user)

        preview = json.loads(task.preview_data)

        # Step 2: running + 立即 commit（前端轮询能看到）
        task.task_status = "running"
        self._add_log(task, user_id, "Worker 开始执行投递任务", step="start")
        self.db.add(task)
        self.db.commit()

        # Step 3: 校验
        errors = self._validate_preview(preview)
        if errors:
            task.task_status = "waiting_user"
            for err in errors:
                self._add_log(task, user_id, err, step="validate", level="warning")
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            return task

        # Step 4: 生成填表清单（模式一/二，替代 Playwright）
        checklist = self._build_fill_checklist(preview)
        self._add_log(
            task, user_id,
            f"已生成 {len(checklist)} 项填表清单",
            step="checklist",
        )
        for item in checklist:
            self._add_log(
                task, user_id,
                f"{item['label']} = {item['value']}",
                step="field",
            )

        # Step 5: 预留 Playwright 扩展点（3.18 再做）
        # result = PlaywrightFormFiller(...).fill(...)

        # Step 6: 成功
        task.task_status = "success"
        self._add_log(
            task, user_id,
            "半自动填表方案已生成；Playwright 自动填表模块待接入。",
            step="finish",
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

    # def _add_log(self, task: DeliveryTask, user_id: int, message: str) -> None:
    #     self.db.add(
    #         DeliveryTaskLog(
    #             task_id=task.id,
    #             user_id=user_id,
    #             level="info",
    #             message=message,
    #         )
    #     )

    def _add_log(
        self,
        task: DeliveryTask,
        user_id: int,
        message: str,
        *,
        level: str = "info",
        step: str | None = None,
    ) -> None:
        text = f"[{step}] {message}" if step else message
        self.db.add(DeliveryTaskLog(
            task_id=task.id,
            user_id=user_id,
            level=level,
            message=text,
        ))
        
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
    
    def build_preview(self, *, task_id: int, user_id: int) -> tuple[DeliveryTask, dict]:
        task = self._get_task(task_id, user_id)
        user = self._require_user(user_id)
        self._build_preview(task, user)
        self.db.refresh(task)
        return task, json.loads(task.preview_data)

    def _validate_preview(self, preview: dict) -> list[str]:
        """返回错误列表；非空则任务进入 waiting_user。"""
        errors: list[str] = []
        url = (preview.get("target_url") or "").strip()
        if not url:
            errors.append("目标投递链接为空，请填写投递链接或使用带 source_url 的岗位")
        elif not url.startswith(("http://", "https://")):
            errors.append(f"目标链接格式无效: {url}")
        fields = preview.get("fields") or {}
        if not str(fields.get("name") or "").strip():
            errors.append("姓名为空，请先完善投递档案")
        if not str(fields.get("email") or "").strip():
            errors.append("邮箱为空，请先完善投递档案")
        return errors

    def _build_fill_checklist(self, preview: dict) -> list[dict]:
        """把 preview 转成可复制的填表清单。"""
        label_map = {
            "name": "姓名",
            "phone": "电话",
            "email": "邮箱",
            "school": "学校",
            "major": "专业",
            "job": "意向岗位",
        }
        fields = preview.get("fields") or {}
        checklist: list[dict] = []
        site_name = (preview.get("site_name") or "").strip()
        if site_name:
            checklist.append({"key": "site", "label": "目标站点", "value": site_name})
        for key, label in label_map.items():
            value = str(fields.get(key) or "").strip()
            if value:
                checklist.append({"key": key, "label": label, "value": value})
        target_url = (preview.get("target_url") or "").strip()
        if target_url:
            checklist.append({"key": "url", "label": "投递链接", "value": target_url})
        return checklist

    def _require_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise BusinessException(code=4040, message="user not found")
        return user
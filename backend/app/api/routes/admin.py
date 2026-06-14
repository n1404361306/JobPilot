from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.response import ok
from app.db.session import get_db
from app.deps.auth import require_permissions
from app.models.system_config import SystemConfig
from app.models.system_log import AICallLog, OCRLog, SystemLog
from app.models.user import User
from app.schemas.admin import ConfigUpdate, UserStatusUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["admin:users:read"])),
):
    users = db.scalars(select(User).order_by(User.id.desc())).all()
    data = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
        }
        for u in users
    ]
    return ok(data)


@router.put("/users/{id}/status")
def update_user_status(
    id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["admin:users:write"])),
):
    user = db.get(User, id)
    if not user:
        raise BusinessException(code=4041, message="user not found")
    user.is_active = payload.is_active
    db.add(user)
    db.commit()
    return ok(message="status updated")


@router.get("/ai-logs")
def ai_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["admin:logs:read"])),
):
    logs = db.scalars(select(AICallLog).order_by(AICallLog.id.desc()).limit(200)).all()
    return ok([
        {
            "id": x.id, 
            "user_id": x.user_id,
            "model_name": x.model_name, 
            "prompt_type": x.prompt_type,
            "input_tokens": x.input_tokens,
            "output_tokens": x.output_tokens,
            "cost_estimate": x.cost_estimate,
            "status": x.status,
            "error_message": x.error_message,
            "duration_ms": x.duration_ms,
            "created_at": x.created_at,
            } for x in logs])


@router.get("/ocr-logs")
def ocr_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["admin:logs:read"])),
):
    logs = db.scalars(select(OCRLog).order_by(OCRLog.id.desc()).limit(200)).all()
    return ok([{"id": x.id, "source_type": x.source_type, "result_summary": x.result_summary} for x in logs])


@router.get("/system-logs")
def system_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["admin:logs:read"])),
):
    logs = db.scalars(select(SystemLog).order_by(SystemLog.id.desc()).limit(200)).all()
    return ok([{"id": x.id, "level": x.level, "message": x.message} for x in logs])


@router.get("/system-configs")
def list_system_configs(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["admin:configs:read"])),
):
    records = db.scalars(select(SystemConfig).order_by(SystemConfig.id.desc())).all()
    return ok([{"key": x.config_key, "value": x.config_value} for x in records])


@router.put("/system-configs/{key}")
def update_system_config(
    key: str,
    payload: ConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions(["admin:configs:write"])),
):
    record = db.scalar(select(SystemConfig).where(SystemConfig.config_key == key))
    if not record:
        record = SystemConfig(config_key=key, config_value=payload.config_value)
    else:
        record.config_value = payload.config_value
    db.add(record)
    db.commit()
    return ok(message="config updated")

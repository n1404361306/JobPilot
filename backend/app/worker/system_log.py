from datetime import datetime

from app.models.system_log import SystemLog


def write_system_log(db, *, level: str, message: str) -> None:
    db.add(SystemLog(level=level, message=message[:2000], created_at=datetime.utcnow()))
    db.commit()
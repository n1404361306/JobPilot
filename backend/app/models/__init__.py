from app.models.business import Application, Job, Resume, ResumeTemplate
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.models.system_config import SystemConfig
from app.models.system_log import AICallLog, OCRLog, SystemLog
from app.models.user import User, UserRole
from app.models.prompt_template import PromptTemplate

__all__ = [
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "SystemConfig",
    "AICallLog",
    "OCRLog",
    "SystemLog",
    "PromptTemplate",
    "Resume",
    "ResumeTemplate",
    "Job",
    "Application",
]

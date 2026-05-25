from typing import Iterable, Optional

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.models.user import User
from app.models.user import UserRole


def _token_from_header(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise BusinessException(code=4011, message="missing bearer token")
    return authorization.replace("Bearer ", "", 1)


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _token_from_header(authorization)
    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise BusinessException(code=4012, message="invalid access token")
    username = payload.get("sub")
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise BusinessException(code=4013, message="user not found")
    if not user.is_active:
        raise BusinessException(code=4014, message="user is disabled")
    return user


def require_roles(roles: Iterable[str]):
    normalized = set(roles)

    def _checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if user.is_superuser:
            return user
        role_codes = db.scalars(
            select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
        ).all()
        if not set(role_codes).intersection(normalized):
            raise BusinessException(code=4031, message="role denied")
        return user

    return _checker


def require_permissions(permissions: Iterable[str]):
    normalized = set(permissions)

    def _checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if user.is_superuser:
            return user
        permission_codes = db.scalars(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
        ).all()
        if not set(permission_codes).issuperset(normalized):
            raise BusinessException(code=4032, message="permission denied")
        return user

    return _checker

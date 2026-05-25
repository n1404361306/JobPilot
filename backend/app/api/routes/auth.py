from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.response import ok
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.models.role import Role
from app.models.user import User
from app.models.user import UserRole
from app.schemas.auth import LoginRequest, PasswordUpdateRequest, RefreshTokenRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existed = db.scalar(select(User).where((User.username == payload.username) | (User.email == payload.email)))
    if existed:
        raise BusinessException(code=4001, message="username or email already exists")
    user = User(username=payload.username, email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    user_role = db.scalar(select(Role).where(Role.code == "user"))
    if user_role:
        db.add(UserRole(user_id=user.id, role_id=user_role.id))
        db.commit()
    return ok({"id": user.id}, "register success")


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise BusinessException(code=4002, message="invalid username or password")
    tokens = TokenResponse(
        access_token=create_token(user.username, token_type="access"),
        refresh_token=create_token(user.username, token_type="refresh"),
    )
    return ok(tokens.model_dump(), "login success")


@router.post("/logout")
def logout():
    return ok(message="logout success")


@router.post("/refresh")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)
    if token_data.get("token_type") != "refresh":
        raise BusinessException(code=4015, message="invalid refresh token")
    username = token_data.get("sub")
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise BusinessException(code=4013, message="user not found")
    tokens = TokenResponse(
        access_token=create_token(user.username, token_type="access"),
        refresh_token=create_token(user.username, token_type="refresh"),
    )
    return ok(tokens.model_dump(), "token refreshed")


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
    )


@router.put("/password")
def update_password(
    payload: PasswordUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise BusinessException(code=4003, message="old password invalid")
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return ok(message="password updated")

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ok
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    return ok(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
    )


@router.put("/me")
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.email = payload.email
    db.add(user)
    db.commit()
    return ok(message="profile updated")

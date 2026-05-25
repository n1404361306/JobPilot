from pydantic import BaseModel, EmailStr


class UserInfo(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_superuser: bool


class UserProfileUpdate(BaseModel):
    email: EmailStr

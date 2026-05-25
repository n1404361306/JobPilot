from pydantic import BaseModel


class UserStatusUpdate(BaseModel):
    is_active: bool


class ConfigUpdate(BaseModel):
    config_value: str

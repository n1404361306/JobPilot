from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None


def ok(data=None, message: str = "ok") -> ApiResponse:
    return ApiResponse(code=0, message=message, data=data)

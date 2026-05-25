from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class BusinessException(Exception):
    def __init__(self, code: int = 4000, message: str = "business error"):
        self.code = code
        self.message = message
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def business_exception_handler(_: Request, exc: BusinessException):
        return JSONResponse(status_code=400, content={"code": exc.code, "message": exc.message, "data": None})

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"code": exc.status_code, "message": exc.detail, "data": None})

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(_: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"code": 422, "message": "validation error", "data": exc.errors()})

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(_: Request, __: Exception):
        return JSONResponse(status_code=500, content={"code": 5000, "message": "internal server error", "data": None})

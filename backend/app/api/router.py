from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.business import router as business_router
from app.api.routes.users import router as users_router
from app.api.routes.ocr import router as ocr_router
from app.api.routes.ai import router as ai_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(business_router)
api_router.include_router(ocr_router)
api_router.include_router(ai_router)

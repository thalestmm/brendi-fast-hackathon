from fastapi import APIRouter

from app.routers.api.v1 import analytics, chat, data

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
)

router.include_router(analytics.router)
router.include_router(chat.router)
router.include_router(data.router)

__all__ = ["router"]

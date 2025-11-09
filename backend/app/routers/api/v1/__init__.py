from fastapi import APIRouter

from app.routers.api.v1 import analytics, chat, data, websocket

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
)

router.include_router(analytics.router)
router.include_router(chat.router)
router.include_router(data.router)
router.include_router(websocket.router)

__all__ = ["router"]

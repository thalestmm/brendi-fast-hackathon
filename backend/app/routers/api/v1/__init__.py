from fastapi import APIRouter

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
)

# TODO: Include routers here

__all__ = ["router"]
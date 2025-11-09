"""
Dependency injection for FastAPI routes.
"""

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session

logger = logging.getLogger(__name__)

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_store_id(
    x_store_id: str = Header(
        ...,
        alias="X-Store-ID",
        description="Store identifier for multi-tenant filtering",
    ),
) -> str:
    """
    Extract and validate store_id from request headers.

    Args:
        x_store_id: Store ID from X-Store-ID header

    Returns:
        Store ID string

    Raises:
        HTTPException: If store_id is missing or invalid
    """
    if not x_store_id or not x_store_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Store-ID header is required",
        )

    # TODO: Validate store_id exists in database
    # For now, just return the provided store_id
    return x_store_id.strip()


# Type alias for store_id dependency
StoreId = Annotated[str, Depends(get_store_id)]


__all__ = ["DbSession", "StoreId", "get_store_id"]

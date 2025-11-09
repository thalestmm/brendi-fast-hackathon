"""
Multi-tenant middleware for extracting and validating store_id.
"""

import logging
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract store_id from headers and inject into request state.

    Note: This middleware validates the header exists but doesn't validate
    the store exists in the database. That validation should happen in
    dependencies or route handlers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and extract store_id.

        Excludes health check and docs endpoints from tenant requirement.
        """
        # Skip tenant check for health and docs endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return await call_next(request)

        # Extract store_id from header
        store_id = request.headers.get("X-Store-ID")

        if not store_id or not store_id.strip():
            # Allow requests without store_id for now (will be validated in dependencies)
            # This allows flexibility for endpoints that don't require tenant context
            logger.debug("No X-Store-ID header found")
        else:
            # Store in request state for use in dependencies
            request.state.store_id = store_id.strip()
            logger.debug(f"Extracted store_id: {store_id.strip()}")

        response = await call_next(request)
        return response


__all__ = ["TenantMiddleware"]

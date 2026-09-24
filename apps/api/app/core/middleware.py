"""
Custom middleware stack.

RequestIDMiddleware: Attaches a unique request ID to every request/response.
SecurityHeadersMiddleware: Adds OWASP-recommended security headers.
CSRFMiddleware: Double Submit Cookie pattern for CSRF protection.
  - Skipped in test environment (ENV=test) so the test suite can run without
    setting up CSRF tokens on every request.
"""

import os
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds baseline OWASP-recommended security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"  # clickjacking protection
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Provides CSRF protection via the Double Submit Cookie pattern.

    Skipped when ENV is 'test' (set by the test conftest) so automated tests
    don't need to manage CSRF tokens. In production and development, every
    mutating request must include both the xsrf-token cookie and the matching
    x-xsrf-token header.
    """

    async def dispatch(self, request: Request, call_next):
        from starlette.responses import JSONResponse

        # Skip CSRF validation in test environment
        env = os.environ.get("ENV", "development")
        if env == "test":
            return await call_next(request)

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            csrf_cookie = request.cookies.get("xsrf-token")
            csrf_header = request.headers.get("x-xsrf-token")

            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                return JSONResponse(
                    status_code=403,
                    content={"error": {"code": "CSRF_ERROR", "message": "CSRF token mismatch"}}
                )

        response = await call_next(request)

        if "xsrf-token" not in request.cookies:
            settings = get_settings()
            response.set_cookie(
                "xsrf-token",
                str(uuid.uuid4()),
                httponly=False,  # JS needs to read it
                secure=settings.COOKIE_SECURE,
                samesite="none" if settings.COOKIE_SECURE else "lax",
                path="/"
            )

        return response

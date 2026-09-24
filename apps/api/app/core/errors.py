import logging
import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")

_STATUS_CODE_TO_ERROR_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def _error_body(code: str, message: str, request_id: str) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    code = _STATUS_CODE_TO_ERROR_CODE.get(exc.status_code, "ERROR")
    return JSONResponse(status_code=exc.status_code, content=_error_body(code, str(exc.detail), request_id))


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    errors = exc.errors()
    message = "One or more fields failed validation"
    if errors and len(errors) > 0:
        message = errors[0].get("msg", message)

    return JSONResponse(
        status_code=422,
        content=_error_body("VALIDATION_ERROR", message, request_id),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    # Log full detail server-side; never leak stack traces / internals to the client (requirement #45)
    logger.exception("Unhandled exception [request_id=%s]", request_id)
    return JSONResponse(
        status_code=500,
        content=_error_body(
            "INTERNAL_ERROR", "An unexpected error occurred. Please try again later.", request_id
        ),
    )

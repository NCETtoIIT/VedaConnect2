"""
VedaConnect Core Error Handling — Consistent error envelope.

Standard error response format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": { ... }
    }
}
"""

import logging
import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger("vedaconnect.errors")


# ═══════════════════════════════════════════════════════════════
#  Error Response Builder
# ═══════════════════════════════════════════════════════════════

def _build_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Build a standardized error JSON response."""
    body: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


# ═══════════════════════════════════════════════════════════════
#  Exception Handlers
# ═══════════════════════════════════════════════════════════════

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with consistent envelope."""
    # Map common status codes to error codes
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    detail_str = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    return _build_error_response(
        status_code=exc.status_code,
        code=error_code,
        message=detail_str,
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError with field-level details."""
    errors = []
    for err in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error"),
        })

    return _build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed. Check the details for specific field errors.",
        details={"errors": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with a safe 500 response (no stack trace leak)."""
    # Log full traceback server-side
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )

    return _build_error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again or contact support.",
    )


# ═══════════════════════════════════════════════════════════════
#  Registration Helper
# ═══════════════════════════════════════════════════════════════

def register_error_handlers(app: FastAPI) -> None:
    """Register all VedaConnect error handlers on a FastAPI app."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

setup_exception_handlers = register_error_handlers

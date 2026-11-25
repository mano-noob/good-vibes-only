from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi.responses import JSONResponse


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def success_response(data: Any) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "generated_at": iso_timestamp(),
            "data": data,
        },
    )


def error_response(message: str, details: Any = None, status_code: int = 500) -> JSONResponse:
    payload: dict[str, Any] = {
        "success": False,
        "message": message,
        "details": details,
    }
    return JSONResponse(status_code=status_code, content=payload)


def exception_response(message: str, exc: Exception) -> JSONResponse:
    frames = traceback.extract_tb(exc.__traceback__)
    origin = frames[-1] if frames else None
    logging.getLogger("trading_agent").error(
        "%s failed (%s) at %s:%s",
        message,
        type(exc).__name__,
        origin.filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1] if origin else "unknown",
        origin.lineno if origin else 0,
    )
    return error_response(message, "An unexpected server error occurred.", 500)

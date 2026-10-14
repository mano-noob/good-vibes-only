from __future__ import annotations

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

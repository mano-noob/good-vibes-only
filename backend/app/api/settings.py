from typing import Any

from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.core.settings_service import SettingsService

router = APIRouter()


@router.get("")
@router.get("/")
def read_settings():
    try:
        return success_response(SettingsService.load())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load settings", str(exc), 500)


@router.get("/defaults")
def read_default_settings():
    try:
        return success_response(SettingsService._default_settings())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to load default settings", str(exc), 500)


@router.post("")
@router.post("/")
def save_settings(payload: dict[str, Any]):
    try:
        merged = SettingsService.load()
        merged.update(payload or {})
        SettingsService.save(merged)
        return success_response(merged)
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to save settings", str(exc), 500)


@router.put("")
@router.put("/")
def update_settings(payload: dict[str, Any]):
    try:
        merged = SettingsService.load()
        merged.update(payload or {})
        SettingsService.save(merged)
        return success_response(merged)
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to update settings", str(exc), 500)

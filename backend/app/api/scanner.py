from fastapi import APIRouter

from app.core.api_response import error_response, success_response
from app.services.scanner_service import ScannerService

router = APIRouter()


@router.get("/scan")
def scan_market():
    try:
        return success_response(ScannerService.scan_market())
    except Exception as exc:  # pragma: no cover - API error handling
        return error_response("Failed to scan market", str(exc), 500)
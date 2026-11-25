from fastapi import APIRouter

from app.core.api_response import exception_response, success_response
from app.services.scanner_service import ScannerService

router = APIRouter()


@router.get("/scan")
def scan_market():
    try:
        return success_response(ScannerService.scan_market())
    except Exception as exc:  # pragma: no cover - API error handling
        return exception_response("Failed to scan market", exc)
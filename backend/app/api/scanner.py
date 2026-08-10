from fastapi import APIRouter
from app.services.scanner_service import ScannerService

router = APIRouter()


@router.get("/scan")
def scan_market():

    return ScannerService.scan_market()
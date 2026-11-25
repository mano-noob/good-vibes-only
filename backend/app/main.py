from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from app.api.alerts import router as alert_router
from app.api.backtest import router as backtest_router
from app.api.decision import router as decision_router
from app.api.market import router as market_router
from app.api.optimization import router as optimization_router
from app.api.portfolio import router as portfolio_router
from app.api.portfolio_backtest import router as portfolio_backtest_router
from app.api.relative_strength import router as rs_router
from app.api.review import router as review_router
from app.api.scanner import router as scanner_router
from app.api.settings import router as settings_router
from app.api.system import router as system_router
from app.api.trading import router as trading_router
from app.core.api_response import error_response, success_response
from app.core.environment import settings
from app.core.logger import LoggerService
from app.services.scheduler_service import shutdown_scheduler, start_scheduler

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    LoggerService.info_event("application_starting")
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()
        LoggerService.info_event("application_stopped")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(_request: Request, exc: FileNotFoundError):
    logging.getLogger("trading_agent").warning("Requested backend file was not found")
    return error_response("File not found", "The requested resource was not found.", 404)


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    return error_response("Invalid value", str(exc), 400)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return error_response(message, exc.detail, exc.status_code)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_request: Request, exc: RequestValidationError):
    details = [
        {key: error[key] for key in ("loc", "msg", "type") if key in error}
        for error in exc.errors()
    ]
    return error_response("Invalid request", details, 422)


@app.exception_handler(Exception)
async def unexpected_exception_handler(_request: Request, exc: Exception):
    logging.getLogger("trading_agent").exception("Unhandled API exception")
    return error_response("Unexpected error", "An unexpected server error occurred.", 500)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            logging.getLogger("trading_agent").warning(
                "API_REQUEST_FAILURE %s %s status=%s",
                request.method,
                request.url.path,
                response.status_code,
            )
        return response
    except Exception:
        logging.getLogger("trading_agent").exception(
            "API_REQUEST_FAILURE %s %s",
            request.method,
            request.url.path,
        )
        raise


app.include_router(market_router, prefix="/api/v1/market", tags=["Market"])
app.include_router(decision_router, prefix="/api/v1/decision", tags=["Decision"])
app.include_router(trading_router, prefix="/api/v1/trading", tags=["Trading"])
app.include_router(alert_router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(scanner_router, prefix="/api/v1/scanner", tags=["Scanner"])
app.include_router(backtest_router, prefix="/api/v1/backtest", tags=["Backtest"])
app.include_router(portfolio_backtest_router, prefix="/api/v1/portfolio-backtest", tags=["Portfolio Backtest"])
app.include_router(optimization_router, prefix="/api/v1/optimize", tags=["Optimization"])
app.include_router(rs_router, prefix="/api/v1/rs", tags=["Relative Strength"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(system_router, prefix="/api/v1/system", tags=["System"])


@app.get("/")
def root():
    return success_response({"message": "AI Trading Agent Running"})


@app.get("/test-env")
def test_env():
    return success_response({
        "bot_token_exists": bool(settings.telegram_bot_token),
        "chat_id_exists": bool(settings.telegram_chat_id),
    })


@app.get("/health")
def health_check():
    return success_response({"status": "healthy"})


app.include_router(review_router, prefix="/api/v1/review", tags=["Review"])
app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["Portfolio"])


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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
from app.services.scheduler_service import start_scheduler

logging.getLogger("trading_agent").info("MAIN FILE LOADED")
logging.getLogger("trading_agent").info("PORTFOLIO IMPORT SUCCESS")

app = FastAPI(title="AI Trading Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(_request: Request, exc: FileNotFoundError):
    return error_response("File not found", str(exc), 404)


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    return error_response("Invalid value", str(exc), 400)


@app.exception_handler(Exception)
async def unexpected_exception_handler(_request: Request, exc: Exception):
    logging.getLogger("trading_agent").exception("Unhandled API exception: %s", exc)
    return error_response("Unexpected error", str(exc), 500)


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
    except Exception as exc:
        logging.getLogger("trading_agent").exception(
            "API_REQUEST_FAILURE %s %s error=%s",
            request.method,
            request.url.path,
            str(exc),
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
    import os

    return success_response({
        "bot_token_exists": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
    })


@app.get("/health")
def health_check():
    return success_response({"status": "healthy"})


@app.on_event("startup")
def startup_event():
    start_scheduler()


app.include_router(review_router, prefix="/api/v1/review", tags=["Review"])
app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["Portfolio"])

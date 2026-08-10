from fastapi import FastAPI
print("MAIN FILE LOADED")
from app.api.scanner import router as scanner_router
from app.api.market import router as market_router
from app.api.trading import router as trading_router
from app.api.alerts import router as alert_router
from app.services.scheduler_service import start_scheduler
from app.api.backtest import router as backtest_router
from app.api.portfolio_backtest import (
    router as portfolio_backtest_router
)
from app.api.optimization import (
    router as optimization_router
)
from app.api.relative_strength import (
    router as rs_router
)
from app.api.review import (
    router as review_router
)
from app.api.decision import (
    router as decision_router
)

print("PORTFOLIO IMPORT SUCCESS")


app = FastAPI(
    title="AI Trading Agent",
    version="1.0.0"
)

app.include_router(
    market_router,
    prefix="/api/v1/market",
    tags=["Market"]
)

app.include_router(

    decision_router,

    prefix="/api/v1/decision",

    tags=["Decision"]

)

app.include_router(
    trading_router,
    prefix="/api/v1/trading",
    tags=["Trading"]
)

app.include_router(
    alert_router,
    prefix="/api/v1/alerts",
    tags=["Alerts"]
)

app.include_router(
    scanner_router,
    prefix="/api/v1/scanner",
    tags=["Scanner"]
)

app.include_router(
    backtest_router,
    prefix="/api/v1/backtest",
    tags=["Backtest"]
)

app.include_router(
    portfolio_backtest_router,
    prefix="/api/v1/portfolio-backtest",
    tags=["Portfolio Backtest"]
)

app.include_router(
    optimization_router,
    prefix="/api/v1/optimize",
    tags=["Optimization"]
)

app.include_router(
    rs_router,
    prefix="/api/v1/rs",
    tags=["Relative Strength"]
)

@app.get("/")
def root():
    return {
        "message": "AI Trading Agent Running"
    }

@app.get("/test-env")
def test_env():

    import os

    return {
        "bot_token_exists": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID")
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.on_event("startup")
def startup_event():

    start_scheduler()

app.include_router(

    review_router,

    prefix="/api/v1/review",

    tags=["Review"]

)
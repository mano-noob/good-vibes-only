# AI Trading Agent

## Overview

This project is a FastAPI-based trading agent that analyzes market conditions, scores watchlists, evaluates portfolio positions, and surfaces review summaries through a service-oriented backend.

## Architecture

- API layer: FastAPI routers for market, trading, review, portfolio, and system endpoints
- Service layer: scoring, scanning, risk, journal, analytics, and scheduler services
- Data layer: JSON-backed runtime state and centralized data paths
- Insights: relative strength, technical indicators, portfolio health, review summaries, and alerts

## Features

- Market scan and relative-strength ranking
- Technical breakout analysis and decision generation
- Portfolio tracking and journal persistence
- Risk and position sizing calculations
- Review generation with summary and alert context
- Scheduled market scan automation

## Folder Structure

```text
backend/
  app/
    api/
    core/
    engines/
    indicators/
    services/
    strategies/
    utils/
  data/
  logs/
  tests/
  requirements.txt
frontend/
README.md
```

## Installation

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running Backend

```bash
cd backend
copy .env.example .env   # Windows; optional
python -m app.main
```

The backend reads deployment settings from `backend/.env` or process environment
variables. Do not put real credentials in `.env.example`. For multi-worker
deployments, the scheduler uses a data-directory process lock so only one worker
runs scheduled jobs. The JSON-backed data directory must be on a filesystem that
supports process locks.

## Running from Windows CMD

Open two Command Prompt windows from the repository root.

Backend:

```bat
cd /d backend
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
if not exist .env copy .env.example .env
python -m app.main
```

Frontend:

```bat
cd /d frontend
npm ci
npm run dev
```

## Running Backend Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

## API Endpoints

Key routes include:

- /api/v1/trading/analyze/{symbol}
- /api/v1/trading/review
- /api/v1/trading/statistics
- /api/v1/portfolio
- /api/v1/portfolio/analytics
- /api/v1/review
- /api/v1/system/health
- /api/v1/system/metrics

## Future Roadmap

- Add persistent database-backed storage
- Expand portfolio analytics and risk dashboards
- Improve backtesting and optimization workflows
- Add richer alerting and reporting capabilities
- Enhance automated strategy tuning and configuration management

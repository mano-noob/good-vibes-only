from app.services.trade_lifecycle_service import TradeLifecycleService


def test_trade_lifecycle_round_trip(tmp_path, monkeypatch):
    trades_file = tmp_path / "trades.json"
    monkeypatch.setattr(TradeLifecycleService, "DATA_FILE", trades_file)

    created = TradeLifecycleService.create_trade({
        "symbol": "TCS.NS",
        "entry_price": 3200.0,
        "quantity": 10,
        "entry_date": "2026-08-01",
    })

    assert created["status"] == "OPEN"
    assert created["symbol"] == "TCS.NS"
    assert TradeLifecycleService.get_open_trade("TCS.NS")["status"] == "OPEN"

    updated = TradeLifecycleService.update_trade("TCS.NS", {
        "current_price": 3400.0,
        "highest_price": 3400.0,
        "lowest_price": 3180.0,
        "current_stop": 3150.0,
        "current_return_pct": 6.25,
        "holding_health": "Healthy",
    })

    assert updated["current_price"] == 3400.0
    assert updated["holding_health"] == "Healthy"

    closed = TradeLifecycleService.close_trade("TCS.NS", exit_price=3500.0, exit_reason="Target hit")
    assert closed["status"] == "CLOSED"
    assert closed["profit_pct"] > 0
    assert closed["profit_amount"] > 0

    assert TradeLifecycleService.get_open_trade("TCS.NS") is None
    assert len(TradeLifecycleService.get_closed_trades()) == 1

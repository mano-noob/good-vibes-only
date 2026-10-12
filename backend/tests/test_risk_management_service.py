from app.services.risk_management_service import RiskManagementService


def test_calculate_trade_uses_settings_and_risk_limits():
    settings = {
        "capital": 100000,
        "risk_per_trade_pct": 2,
        "atr_multiplier": 2,
        "target_rr": 2.5,
    }

    result = RiskManagementService.calculate_trade(
        entry_price=5100,
        atr=55,
        available_cash=100000,
        settings=settings,
    )

    assert result["risk_amount"] == 2000
    assert result["initial_stop"] == 4990
    assert result["risk_reward"] == 2.5
    assert result["target_price"] == 5375
    assert result["position_size"] > 0
    assert "allocation_pct" in result

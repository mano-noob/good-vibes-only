import unittest

from app.services.position_service import PositionService


class PositionServiceTests(unittest.TestCase):
    def test_calculate_position_health_and_metrics(self):
        position = {
            "symbol": "TITAN.NS",
            "quantity": 10,
            "entry_price": 4800,
            "entry_date": "2026-08-10",
            "initial_stop": 4600,
            "current_stop": 4700,
            "highest_price": 5000,
            "strategy": "breakout",
            "status": "OPEN",
            "notes": ""
        }

        analysis = {
            "symbol": "TITAN.NS",
            "close_price": 4950,
            "ema20": 4890,
            "ema50": 4850,
            "ema200": 4700,
            "rsi": 62,
            "atr": 95,
            "relative_strength": 72,
            "signal": {"diagnostics": {"trend_confirmation": True}},
        }

        metrics = PositionService.calculate_position_metrics(position, analysis)
        self.assertEqual(metrics["current_price"], 4950)
        self.assertEqual(metrics["market_value"], 49500)
        self.assertEqual(metrics["cost_basis"], 48000)
        self.assertEqual(metrics["profit_amount"], 1500)
        self.assertAlmostEqual(metrics["profit_pct"], 3.13, places=2)
        self.assertEqual(metrics["highest_price"], 5000)
        self.assertEqual(metrics["current_stop"], 4810.0)

        health = PositionService.calculate_position_health(position, analysis, metrics)
        self.assertIn(health, ["Healthy", "Under Watch", "Weakening", "Exit Candidate"])

    def test_trailing_stop_never_moves_downward(self):
        position = {
            "symbol": "TITAN.NS",
            "quantity": 10,
            "entry_price": 4800,
            "entry_date": "2026-08-10",
            "initial_stop": 4600,
            "current_stop": 4700,
            "highest_price": 5000,
            "strategy": "breakout",
            "status": "OPEN",
            "notes": ""
        }

        new_stop = PositionService.calculate_trailing_stop(position, current_price=4900, atr=90)
        self.assertEqual(new_stop, 4820.0)


if __name__ == "__main__":
    unittest.main()

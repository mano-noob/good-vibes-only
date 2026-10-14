import { useEffect, useMemo, useState } from "react";
import { fetchPortfolio } from "../services/portfolioService";

export function usePortfolio() {
  const [data, setData] = useState({ positions: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPortfolio = async () => {
    setLoading(true);
    setError("");

    try {
      const portfolioData = await fetchPortfolio();
      setData(portfolioData);
    } catch (err) {
      setError(err?.response?.data?.message || "Portfolio data unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortfolio();
  }, []);

  const rows = useMemo(
    () =>
      (data.positions || []).map((holding, index) => {
        const quantity = Number(holding.quantity || 0);
        const entryPrice = Number(holding.entry_price || 0);
        const currentPrice = Number(holding.current_price || entryPrice || 0);
        const marketValue = quantity * currentPrice;
        const pnl = (currentPrice - entryPrice) * quantity;
        const pnlPercent = entryPrice
          ? ((currentPrice - entryPrice) / entryPrice) * 100
          : 0;

        return {
          id: holding.symbol || holding.name || `position-${index}`,
          symbol: holding.symbol || "N/A",
          quantity,
          entry: entryPrice,
          current: currentPrice,
          marketValue,
          pnl,
          pnlPercent,
          decision: holding.decision?.action || holding.entry_signal || "HOLD",
          priority: holding.priority || holding.entry_priority || "N/A",
        };
      }),
    [data],
  );

  const portfolioPnl = rows.reduce((sum, row) => sum + Number(row.pnl || 0), 0);
  const portfolio = data || { cash: 0, positions: [] };
  const pnlPercent = Number(portfolio.invested || 0)
    ? (portfolioPnl / Math.max(Number(portfolio.invested || 1), 1)) * 100
    : 0;

  return {
    data,
    loading,
    error,
    rows,
    portfolio,
    portfolioPnl,
    pnlPercent,
    reload: loadPortfolio,
  };
}

export default usePortfolio;

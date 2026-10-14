import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client";
import { normalizePayload } from "../utils/formatters";
import {
  buildAlerts,
  buildHoldings,
  buildRecentChanges,
  buildReadinessDistribution,
  buildTopWatchlist,
  emptyReview,
} from "../utils/dashboard";

export function useDashboard() {
  const [review, setReview] = useState(emptyReview);
  const [portfolio, setPortfolio] = useState({ positions: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    setLoading(true);
    setError("");

    try {
      const [reviewResponse, portfolioResponse] = await Promise.all([
        apiClient.get("/trading/review"),
        apiClient.get("/portfolio"),
      ]);

      const payload = normalizePayload(reviewResponse, emptyReview);
      const portfolioData = normalizePayload(portfolioResponse, {
        positions: [],
      });

      setReview(payload);
      setPortfolio(portfolioData);
    } catch (err) {
      const reason =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Unknown error";
      setError(reason);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const summary = review.summary || emptyReview.summary;
  const portfolioSummary =
    review.portfolio_summary || emptyReview.portfolio_summary;
  const holdings = useMemo(
    () => buildHoldings(review, portfolio.positions || []),
    [review, portfolio],
  );
  const watchlist = review.watchlist || [];
  const topWatchlist = useMemo(() => buildTopWatchlist(watchlist), [watchlist]);
  const bestOpportunity = topWatchlist[0] || {};
  const alertsList = useMemo(() => buildAlerts(review), [review]);
  const recentChanges = useMemo(() => buildRecentChanges(review), [review]);
  const readinessDistributionData = useMemo(
    () => buildReadinessDistribution(watchlist, holdings),
    [watchlist, holdings],
  );

  return {
    review,
    portfolio,
    loading,
    error,
    summary,
    portfolioSummary,
    holdings,
    watchlist,
    topWatchlist,
    bestOpportunity,
    alertsList,
    recentChanges,
    readinessDistributionData,
    fetchDashboardData,
  };
}

export default useDashboard;

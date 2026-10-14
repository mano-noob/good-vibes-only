import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client";
import {
  formatMoney,
  formatReviewDate,
  normalizePayload,
} from "../utils/formatters";

export function useJournal() {
  const [journalEntries, setJournalEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const getTotalChanges = (review) => {
    const changeSet = review?.changes || {};

    return Object.values(changeSet).reduce((sum, value) => {
      if (Array.isArray(value)) {
        return sum + value.length;
      }
      return sum;
    }, 0);
  };

  const loadJournalEntries = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.get("/portfolio/journal");
      const payload = normalizePayload(response, []);
      const entries = Array.isArray(payload) ? [...payload].reverse() : [];

      setJournalEntries(
        entries.map((review, index) => {
          const totalBuy = Array.isArray(review.buy) ? review.buy.length : 0;
          const totalHold = Array.isArray(review.hold) ? review.hold.length : 0;
          const totalExit = Array.isArray(review.exit) ? review.exit.length : 0;
          const totalWatchlist = Array.isArray(review.watchlist)
            ? review.watchlist.length
            : 0;
          const alertCount = Array.isArray(review.alerts)
            ? review.alerts.length
            : 0;
          const portfolioValue =
            review.portfolio_summary?.portfolio_value ??
            review.summary?.portfolio?.net_worth ??
            0;

          return {
            ...review,
            id: `${review.review_date || index}-accordion`,
            totalBuy,
            totalHold,
            totalExit,
            totalWatchlist,
            alertCount,
            portfolioValue,
            totalChanges: getTotalChanges(review),
            formattedDate: formatReviewDate(review.review_date),
            formattedPortfolioValue: formatMoney(portfolioValue),
          };
        }),
      );
    } catch (err) {
      const reason =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Journal unavailable.";
      setJournalEntries([]);
      setError(reason);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJournalEntries();
  }, []);

  return {
    journalEntries,
    loading,
    error,
    reload: loadJournalEntries,
    formatReviewDate,
    formatMoney,
  };
}

export default useJournal;

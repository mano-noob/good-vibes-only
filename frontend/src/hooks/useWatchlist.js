import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client";
import { normalizePayload } from "../utils/formatters";

export function useWatchlist() {
  const [rows, setRows] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadWatchlist = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.get("/portfolio/watchlist");
      const payload = normalizePayload(response, []);
      const nextRows = Array.isArray(payload)
        ? payload.map((row, index) => ({
            ...row,
            id: row.id ?? row.symbol ?? index + 1,
            rank: row.rank ?? index + 1,
          }))
        : [];

      setRows(nextRows);
    } catch (err) {
      const reason =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Watchlist unavailable.";
      setRows([]);
      setError(reason);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWatchlist();
  }, []);

  const filteredRows = useMemo(() => {
    const search = query.trim().toLowerCase();
    if (!search) return rows;

    return rows.filter((row) =>
      Object.values(row).some((value) =>
        String(value).toLowerCase().includes(search),
      ),
    );
  }, [query, rows]);

  return {
    rows,
    setRows,
    query,
    setQuery,
    filteredRows,
    loading,
    error,
    reload: loadWatchlist,
  };
}

export default useWatchlist;

export const emptyReview = {
  market_regime: "",
  portfolio_summary: {
    cash: 0,
    market_value: 0,
    portfolio_value: 0,
    unrealized_pnl: 0,
  },
  summary: {
    market: "",
    portfolio: {
      net_worth: 0,
      cash: 0,
      invested: 0,
      positions: 0,
      unrealized_pnl: 0,
    },
    holdings: { healthy: 0, weakening: 0, exit: 0 },
    review: {
      new_buy: 0,
      new_watchlist: 0,
      removed_watchlist: 0,
      major_upgrades: 0,
      major_downgrades: 0,
    },
    best_opportunity: { symbol: "", priority: "", readiness: 0 },
  },
  hold: [],
  watchlist: [],
  changes: { holding_changes: [], readiness_changes: [] },
  alerts: [],
};

export const buildPortfolioMap = (positions = []) =>
  (positions || []).reduce((map, position) => {
    if (position.symbol) {
      map[position.symbol] = position;
    }
    return map;
  }, {});

export const buildHoldings = (review, portfolioPositions = []) => {
  const portfolioBySymbol = buildPortfolioMap(portfolioPositions);

  return (review.hold || []).map((holding) => ({
    ...holding,
    quantity: Number(
      holding.quantity ?? portfolioBySymbol[holding.symbol]?.quantity ?? 0,
    ),
  }));
};

export const buildTopWatchlist = (watchlist = []) =>
  [...watchlist]
    .sort((a, b) => {
      const rankMap = { A: 4, B: 3, C: 2, D: 1, IGNORE: 0 };
      const aRank = rankMap[String(a.priority || "IGNORE").toUpperCase()] || 0;
      const bRank = rankMap[String(b.priority || "IGNORE").toUpperCase()] || 0;

      return (
        bRank - aRank ||
        Number(b.readiness_score || 0) - Number(a.readiness_score || 0) ||
        Number(b.relative_strength || 0) - Number(a.relative_strength || 0)
      );
    })
    .slice(0, 5);

export const buildAlerts = (review) =>
  [...(review.alerts || [])]
    .reverse()
    .map((alert, index) => {
      const type = String(
        alert.type || alert.category || "ALERT",
      ).toUpperCase();
      const titleMap = {
        HOLD: "Holding Status Changed",
        BUY: "New Buy Candidate",
        EXIT: "Exit Signal",
        WATCHLIST: "Watchlist Addition",
        PORTFOLIO: "Portfolio Updated",
      };

      return {
        ...alert,
        title:
          alert.title ||
          titleMap[type] ||
          alert.type ||
          alert.category ||
          `Alert ${index + 1}`,
        message:
          alert.message ||
          alert.description ||
          `Alert from ${alert.symbol || "market watch"}.`,
        severity:
          alert.severity ||
          alert.level ||
          (type === "EXIT"
            ? "high"
            : type === "BUY"
              ? "low"
              : type === "WATCHLIST"
                ? "info"
                : "medium"),
        timestamp:
          alert.timestamp || alert.created_at || new Date().toISOString(),
      };
    })
    .slice(0, 10);

export const buildRecentChanges = (review) =>
  [
    ...(review.changes?.readiness_changes || []).map((change) => {
      const direction =
        change.direction === "UP"
          ? "UP"
          : change.direction === "DOWN"
            ? "DOWN"
            : "CHANGE";

      return {
        type: direction,
        symbol: change.symbol || "Symbol",
        title: "Readiness",
        message:
          change.direction === "UP"
            ? `${change.previous_score ?? 0} → ${change.current_score ?? 0}`
            : `${change.previous_score ?? 0} → ${change.current_score ?? 0}`,
        detail:
          change.direction === "UP"
            ? "Readiness improved"
            : change.direction === "DOWN"
              ? "Readiness weakened"
              : "Readiness updated",
        timestamp: new Date().toISOString(),
      };
    }),
    ...(review.changes?.new_watchlist || []).map((symbol) => ({
      type: "NEW",
      symbol,
      title: "NEW",
      message: `${symbol} added to watchlist`,
      detail: "Added to watchlist",
      timestamp: new Date().toISOString(),
    })),
    ...(review.changes?.removed_watchlist || []).map((symbol) => ({
      type: "REMOVED",
      symbol,
      title: "REMOVED",
      message: `${symbol} dropped from watchlist`,
      detail: "Dropped from watchlist",
      timestamp: new Date().toISOString(),
    })),
    ...(review.changes?.holding_changes || []).map((change) => ({
      type: change.reason ? "CHANGE" : "EVENT",
      symbol: change.symbol || "Holding",
      title: change.symbol || "Holding",
      message:
        change.reason ||
        `${change.from || "Unknown"} → ${change.to || "Unknown"}`,
      detail: change.reason || "Position update",
      timestamp: new Date().toISOString(),
    })),
  ]
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 10);

export const buildReadinessDistribution = (watchlist = [], holdings = []) => {
  const buckets = [
    { name: "0-25", value: 0 },
    { name: "26-50", value: 0 },
    { name: "51-75", value: 0 },
    { name: "76-100", value: 0 },
  ];

  [...watchlist, ...holdings].forEach((item) => {
    const numericScore = Number(item?.readiness_score || 0);
    if (numericScore <= 25) buckets[0].value += 1;
    else if (numericScore <= 50) buckets[1].value += 1;
    else if (numericScore <= 75) buckets[2].value += 1;
    else buckets[3].value += 1;
  });

  return buckets;
};

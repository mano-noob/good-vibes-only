import {
  Alert,
  Box,
  Card,
  CardContent,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import AlertCard from "../cards/AlertCard";
import HoldingCard from "../cards/HoldingCard";
import WatchlistCard from "../cards/WatchlistCard";

function DashboardLists({
  holdings = [],
  alertsList = [],
  topWatchlist = [],
  recentChanges = [],
  bestOpportunity = {},
  summary = {},
}) {
  const fallbackBest = summary.best_opportunity || bestOpportunity;

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, md: 6 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Current Holdings
        </Typography>
        <Stack spacing={2}>
          {holdings.length ? (
            holdings.map((holding) => (
              <HoldingCard
                key={holding.symbol}
                symbol={holding.symbol}
                quantity={holding.quantity || 0}
                entryPrice={holding.entry_price ?? holding.entry ?? 0}
                currentPrice={holding.current_price ?? holding.price ?? 0}
                marketValue={holding.market_value ?? 0}
                pnl={holding.profit_amount ?? holding.pnl ?? 0}
                pnlPercent={holding.pnl_percent ?? holding.profit_percent ?? 0}
                decision={
                  holding.decision?.action || holding.entry_signal || "HOLD"
                }
                readiness={
                  holding.readiness_score ?? holding.readiness ?? "N/A"
                }
                priority={holding.priority || holding.entry_priority || "N/A"}
                status={holding.holding_health || "Healthy"}
              />
            ))
          ) : (
            <Alert severity="info">No current holdings.</Alert>
          )}
        </Stack>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Alerts
        </Typography>
        <Box sx={{ maxHeight: 350, overflowY: "auto", pr: 1 }}>
          <Stack spacing={2}>
            {alertsList.length ? (
              alertsList.map((alert, index) => (
                <AlertCard
                  key={`${alert.title || "alert"}-${index}`}
                  title={alert.title || "Alert"}
                  message={alert.message || "No details provided"}
                  severity={alert.severity || "medium"}
                  timestamp={alert.timestamp || new Date().toISOString()}
                />
              ))
            ) : (
              <Alert severity="info">No alerts available.</Alert>
            )}
          </Stack>
        </Box>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Top Watchlist
        </Typography>
        <Box sx={{ maxHeight: 420, overflowY: "auto", pr: 1 }}>
          <Stack spacing={2}>
            {topWatchlist.length ? (
              topWatchlist.map((item) => (
                <WatchlistCard
                  key={item.symbol}
                  symbol={item.symbol}
                  priority={item.priority || "N/A"}
                  readiness={item.readiness_score || 0}
                  relativeStrength={item.relative_strength || 0}
                  rsi={item.rsi || 0}
                  signal={item.signal?.signal || item.signal || "N/A"}
                  explanation={item.explanation || "No explanation provided"}
                />
              ))
            ) : (
              <Alert severity="info">
                No watchlist data currently available.
              </Alert>
            )}
          </Stack>
        </Box>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Recent Changes
        </Typography>
        <Box sx={{ maxHeight: 420, overflowY: "auto", pr: 1 }}>
          {recentChanges.length ? (
            <Stack spacing={1.5} sx={{ position: "relative", pl: 1 }}>
              {recentChanges.map((change, index) => {
                const accent =
                  change.type === "DOWN" || change.type === "REMOVED"
                    ? "error.main"
                    : change.type === "UP" || change.type === "NEW"
                      ? "success.main"
                      : "info.main";
                const emoji =
                  change.type === "UP"
                    ? "↑"
                    : change.type === "DOWN"
                      ? "↓"
                      : change.type === "NEW"
                        ? "NEW"
                        : change.type === "REMOVED"
                          ? "REMOVED"
                          : "•";

                return (
                  <Box
                    key={`${change.symbol || "change"}-${index}`}
                    sx={{
                      display: "flex",
                      gap: 1.5,
                      alignItems: "flex-start",
                      position: "relative",
                      pl: 1,
                      "&:before": {
                        content: '""',
                        position: "absolute",
                        left: 8,
                        top: 0,
                        bottom: 0,
                        width: 2,
                        borderRadius: 999,
                        background: "rgba(255,255,255,0.12)",
                      },
                    }}
                  >
                    <Box
                      sx={{
                        position: "relative",
                        width: 14,
                        height: 14,
                        borderRadius: "50%",
                        backgroundColor: accent,
                        boxShadow: `0 0 0 3px ${accent}22`,
                        mt: 0.8,
                        flexShrink: 0,
                      }}
                    />
                    <Card
                      sx={{
                        flex: 1,
                        borderLeft: `3px solid ${accent}`,
                        background: "rgba(30,30,30,0.9)",
                      }}
                    >
                      <CardContent sx={{ p: 1.5, pb: "12px !important" }}>
                        <Stack spacing={0.5}>
                          <Typography
                            variant="caption"
                            sx={{
                              color: accent,
                              fontWeight: 700,
                              letterSpacing: 0.5,
                            }}
                          >
                            {emoji} {change.type}
                          </Typography>
                          <Typography
                            variant="subtitle2"
                            sx={{ fontWeight: 700 }}
                          >
                            {change.symbol || "Change"}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {change.title === "Readiness"
                              ? "Readiness"
                              : change.detail || change.title}
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {change.message}
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Box>
                );
              })}
            </Stack>
          ) : (
            <Alert severity="info">
              No significant changes in the latest review.
            </Alert>
          )}
        </Box>
      </Grid>
    </Grid>
  );
}

export default DashboardLists;

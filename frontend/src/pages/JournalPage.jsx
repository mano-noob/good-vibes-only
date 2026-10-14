import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import LoadingState from "../components/LoadingState";
import useJournal from "../hooks/useJournal";

const summaryItems = [
  { label: "Buy Count", key: "buy" },
  { label: "Hold Count", key: "hold" },
  { label: "Exit Count", key: "exit" },
  { label: "Watchlist Count", key: "watchlist" },
  { label: "Changes", key: "changes" },
  { label: "Alerts Generated", key: "alerts" },
  { label: "Portfolio Value", key: "portfolio" },
];

function JournalPage() {
  const {
    journalEntries,
    loading,
    error,
    reload,
    formatReviewDate,
    formatMoney,
  } = useJournal();

  return (
    <LoadingState loading={loading} error={error} onRetry={reload}>
      <Stack spacing={3}>
        <Typography variant="h4">Journal</Typography>

        {journalEntries.length === 0 ? (
          <Alert severity="info">No journal entries are available yet.</Alert>
        ) : (
          <Stack spacing={2}>
            {journalEntries.map((review, index) => (
              <Accordion
                key={review.id}
                defaultExpanded={index === 0}
                sx={{
                  bgcolor: "background.paper",
                  borderRadius: 2,
                  overflow: "hidden",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Stack
                    direction={{ xs: "column", md: "row" }}
                    spacing={2}
                    sx={{
                      width: "100%",
                      justifyContent: "space-between",
                      alignItems: { xs: "flex-start", md: "center" },
                    }}
                  >
                    <Stack>
                      <Typography variant="subtitle2" color="text.secondary">
                        Review Date
                      </Typography>
                      <Typography variant="h6">
                        {formatReviewDate(review.review_date)}
                      </Typography>
                    </Stack>

                    <Chip
                      label={review.market_regime || "Unknown"}
                      color="primary"
                      variant="outlined"
                      sx={{ minWidth: 120 }}
                    />

                    <Stack
                      direction="row"
                      spacing={1}
                      useFlexGap
                      sx={{ flexWrap: "wrap" }}
                    >
                      {summaryItems.map((item) => {
                        const value =
                          item.key === "buy"
                            ? review.totalBuy
                            : item.key === "hold"
                              ? review.totalHold
                              : item.key === "exit"
                                ? review.totalExit
                                : item.key === "watchlist"
                                  ? review.totalWatchlist
                                  : item.key === "changes"
                                    ? review.totalChanges
                                    : item.key === "alerts"
                                      ? review.alertCount
                                      : review.formattedPortfolioValue;

                        return (
                          <Chip
                            key={`${review.id}-${item.key}`}
                            label={`${item.label}: ${value}`}
                            size="small"
                            color={
                              item.key === "portfolio" ? "success" : "default"
                            }
                            variant="filled"
                          />
                        );
                      })}
                    </Stack>
                  </Stack>
                </AccordionSummary>

                <AccordionDetails sx={{ px: 3, pb: 3 }}>
                  <Stack spacing={3}>
                    <Box>
                      <Typography
                        variant="subtitle2"
                        color="text.secondary"
                        sx={{ mb: 1 }}
                      >
                        Review Overview
                      </Typography>
                      <Stack
                        direction="row"
                        spacing={1}
                        useFlexGap
                        sx={{ flexWrap: "wrap" }}
                      >
                        <Chip
                          label={`Buy: ${review.totalBuy}`}
                          color="success"
                        />
                        <Chip
                          label={`Hold: ${review.totalHold}`}
                          color="info"
                        />
                        <Chip
                          label={`Exit: ${review.totalExit}`}
                          color="error"
                        />
                        <Chip
                          label={`Watchlist: ${review.totalWatchlist}`}
                          color="warning"
                        />
                        <Chip
                          label={`Changes: ${review.totalChanges}`}
                          color="secondary"
                        />
                        <Chip
                          label={`Alerts: ${review.alertCount}`}
                          color="primary"
                        />
                        <Chip
                          label={`Portfolio Value: ${review.formattedPortfolioValue}`}
                          color="success"
                        />
                      </Stack>
                    </Box>

                    <Stack spacing={2}>
                      <Typography variant="h6">Watchlist</Typography>
                      {Array.isArray(review.watchlist) &&
                      review.watchlist.length > 0 ? (
                        <List
                          dense
                          sx={{
                            bgcolor: "rgba(255,255,255,0.02)",
                            borderRadius: 2,
                          }}
                        >
                          {review.watchlist.map((stock, stockIndex) => (
                            <ListItem
                              key={`${stock.symbol || stockIndex}-watchlist`}
                              divider
                            >
                              <ListItemText
                                primary={stock.symbol || "Unknown stock"}
                                secondary={
                                  <Stack
                                    direction="row"
                                    spacing={1}
                                    useFlexGap
                                    sx={{ flexWrap: "wrap" }}
                                  >
                                    <Typography variant="caption">
                                      Priority: {stock.priority || "N/A"}
                                    </Typography>
                                    <Typography variant="caption">
                                      Readiness:{" "}
                                      {stock.readiness_score ?? "N/A"}
                                    </Typography>
                                    <Typography variant="caption">
                                      Signal:{" "}
                                      {stock.signal?.signal ||
                                        stock.decision?.action ||
                                        "N/A"}
                                    </Typography>
                                  </Stack>
                                }
                              />
                            </ListItem>
                          ))}
                        </List>
                      ) : (
                        <Typography color="text.secondary">
                          No watchlist items for this review.
                        </Typography>
                      )}
                    </Stack>

                    <Stack spacing={2}>
                      <Typography variant="h6">Readiness Changes</Typography>
                      {Array.isArray(review.changes?.readiness_changes) &&
                      review.changes.readiness_changes.length > 0 ? (
                        <List
                          dense
                          sx={{
                            bgcolor: "rgba(255,255,255,0.02)",
                            borderRadius: 2,
                          }}
                        >
                          {review.changes.readiness_changes.map(
                            (change, changeIndex) => (
                              <ListItem
                                key={`${change.symbol || changeIndex}-readiness`}
                                divider
                              >
                                <ListItemText
                                  primary={change.symbol || "Unknown stock"}
                                  secondary={`${change.previous_score ?? "-"} → ${change.current_score ?? "-"} (${change.direction || "change"})`}
                                />
                              </ListItem>
                            ),
                          )}
                        </List>
                      ) : (
                        <Typography color="text.secondary">
                          No readiness changes recorded.
                        </Typography>
                      )}
                    </Stack>

                    <Stack spacing={2}>
                      <Typography variant="h6">Portfolio Summary</Typography>
                      <Stack
                        direction="row"
                        spacing={1}
                        useFlexGap
                        sx={{ flexWrap: "wrap" }}
                      >
                        <Chip
                          label={`Market Regime: ${review.market_regime || "N/A"}`}
                          color="primary"
                        />
                        <Chip
                          label={`Portfolio Value: ${formatMoney(review.portfolioValue)}`}
                          color="success"
                        />
                      </Stack>
                    </Stack>
                  </Stack>
                </AccordionDetails>
              </Accordion>
            ))}
          </Stack>
        )}
      </Stack>
    </LoadingState>
  );
}

export default JournalPage;

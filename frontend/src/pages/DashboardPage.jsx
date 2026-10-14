import { Box, Stack, Typography } from "@mui/material";
import LoadingState from "../components/LoadingState";
import DashboardCharts from "../components/dashboard/DashboardCharts";
import DashboardLists from "../components/dashboard/DashboardLists";
import DashboardMetrics from "../components/dashboard/DashboardMetrics";
import useDashboard from "../hooks/useDashboard";

function DashboardPage() {
  const {
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
  } = useDashboard();

  const review = {
    summary,
    portfolio_summary: portfolioSummary,
    watchlist,
    hold: holdings,
  };

  return (
    <LoadingState loading={loading} error={error} onRetry={fetchDashboardData}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Market overview and portfolio health
          </Typography>
        </Box>

        <DashboardMetrics
          review={review}
          summary={summary}
          portfolioSummary={portfolioSummary}
        />

        <DashboardLists
          holdings={holdings}
          alertsList={alertsList}
          topWatchlist={topWatchlist}
          recentChanges={recentChanges}
          bestOpportunity={bestOpportunity}
          summary={summary}
        />

        <DashboardCharts
          holdings={holdings}
          watchlist={watchlist}
          portfolioSummary={portfolioSummary}
          summary={summary}
          readinessDistributionData={readinessDistributionData}
        />
      </Stack>
    </LoadingState>
  );
}

export default DashboardPage;

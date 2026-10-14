import { Grid } from "@mui/material";
import OpportunityCard from "../cards/OpportunityCard";
import SummaryCard from "../cards/SummaryCard";

function DashboardMetrics({
  review = {},
  summary = {},
  portfolioSummary = {},
}) {
  const bestOpportunity = summary.best_opportunity || {};

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <SummaryCard
          title="Market Regime"
          value={review.market_regime || summary.market || "Unknown"}
          color="primary.main"
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <SummaryCard
          title="Cash"
          value={`₹${Number(portfolioSummary.cash || 0).toLocaleString()}`}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <SummaryCard
          title="Portfolio Value"
          value={`₹${Number(portfolioSummary.portfolio_value || 0).toLocaleString()}`}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
        <SummaryCard
          title="PnL"
          value={`₹${Number(portfolioSummary.unrealized_pnl || 0).toLocaleString()}`}
          color={
            Number(portfolioSummary.unrealized_pnl || 0) >= 0
              ? "success.main"
              : "error.main"
          }
        />
      </Grid>

      <Grid size={{ xs: 12, md: 4 }}>
        <OpportunityCard
          symbol={bestOpportunity.symbol || "N/A"}
          priority={bestOpportunity.priority || "N/A"}
          signal={
            bestOpportunity.signal?.signal ||
            bestOpportunity.signal ||
            "NO SIGNAL"
          }
          readiness={
            bestOpportunity.readiness_score ?? bestOpportunity.readiness ?? 0
          }
          relativeStrength={bestOpportunity.relative_strength}
          rsi={bestOpportunity.rsi}
          atr={bestOpportunity.atr}
          explanation={bestOpportunity.explanation || "No proper consolidation"}
        />
      </Grid>
      <Grid size={{ xs: 12, md: 4 }}>
        <SummaryCard
          title="Healthy Holdings"
          value={summary.holdings?.healthy || 0}
        />
      </Grid>
      <Grid size={{ xs: 12, md: 4 }}>
        <SummaryCard
          title="Exit Signals"
          value={summary.holdings?.exit || 0}
          color="error.main"
        />
      </Grid>
    </Grid>
  );
}

export default DashboardMetrics;

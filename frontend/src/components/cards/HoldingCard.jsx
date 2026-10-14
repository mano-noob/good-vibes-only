import { Box, Card, CardContent, Grid, Stack, Typography } from "@mui/material";
import PriorityChip from "../chips/PriorityChip";
import StatusChip from "../chips/StatusChip";

function HoldingCard({
  symbol,
  quantity,
  entryPrice,
  currentPrice,
  marketValue,
  pnl,
  pnlPercent,
  decision,
  readiness,
  priority,
  status = "Healthy",
}) {
  const numericPnl =
    Number(
      String(pnl ?? 0)
        .replace(/[^0-9.-]/g, "")
        .replace(/(?!^-)-/g, ""),
    ) || 0;

  const numericPnlPercent =
    Number(
      String(pnlPercent ?? 0)
        .replace(/[^0-9.-]/g, "")
        .replace(/(?!^-)-/g, ""),
    ) || 0;

  const valueColor = numericPnl >= 0 ? "success.main" : "error.main";
  const pnlValue = `₹${Number(Math.abs(numericPnl)).toLocaleString()}`;

  return (
    <Card
      sx={{
        height: "100%",
        borderLeft: "1px solid rgba(255,255,255,0.06)",
        background: "rgba(30,30,30,0.9)",
      }}
    >
      <CardContent sx={{ p: 2.25 }}>
        <Stack
          direction="row"
          sx={{
            mb: 1.5,
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {symbol}
          </Typography>
          <StatusChip decision={decision} />
        </Stack>

        <Grid container spacing={1.5}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Stack spacing={1}>
              <Row label="Quantity" value={quantity} />
              <Row label="Entry Price" value={entryPrice ?? "N/A"} prefix="₹" />
              <Row
                label="Current Price"
                value={currentPrice ?? "N/A"}
                prefix="₹"
              />
              <Row
                label="Market Value"
                value={marketValue ?? "N/A"}
                prefix="₹"
              />
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <Stack spacing={1}>
              <Row
                label="PnL"
                value={numericPnl >= 0 ? `${pnlValue}` : `- ${pnlValue}`}
                valueColor={valueColor}
              />
              <Row
                label="PnL %"
                value={
                  numericPnlPercent >= 0
                    ? `${Math.abs(numericPnlPercent).toFixed(2)}%`
                    : `- ${Math.abs(numericPnlPercent).toFixed(2)}%`
                }
                valueColor={valueColor}
              />
              <Row label="Readiness" value={readiness ?? "N/A"} />
              <Row
                label="Priority"
                value={<PriorityChip priority={priority} />}
                isCustom
              />
            </Stack>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

function Row({ label, value, prefix = "", valueColor, isCustom = false }) {
  const displayValue = isCustom
    ? value
    : typeof value === "number"
      ? `${prefix}${Number(value || 0).toLocaleString()}`
      : (value ?? "N/A");

  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      {isCustom ? (
        <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
          {displayValue}
        </Box>
      ) : (
        <Typography
          variant="body2"
          fontWeight={700}
          sx={{ color: valueColor || "text.primary" }}
        >
          {displayValue}
        </Typography>
      )}
    </Box>
  );
}

export default HoldingCard;

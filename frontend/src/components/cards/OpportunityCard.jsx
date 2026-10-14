import { Box, Card, CardContent, Stack, Typography } from "@mui/material";
import PriorityChip from "../chips/PriorityChip";
import SignalChip from "../chips/SignalChip";

function OpportunityCard({
  symbol,
  priority,
  signal,
  readiness,
  relativeStrength,
  rsi,
  atr,
  explanation,
}) {
  const formatValue = (value, digits = 1) => {
    const num = Number(value);
    if (Number.isNaN(num)) return "N/A";
    return num.toFixed(digits);
  };

  return (
    <Card
      sx={{
        height: "100%",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))",
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Stack spacing={1.5}>
          <Typography
            variant="overline"
            color="text.secondary"
            sx={{ letterSpacing: 0.8 }}
          >
            Best Opportunity
          </Typography>

          <Typography variant="h5" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
            {symbol || "N/A"}
          </Typography>

          <Stack
            direction="row"
            spacing={1}
            sx={{ alignItems: "center", flexWrap: "wrap" }}
          >
            <PriorityChip priority={priority} />
            <SignalChip signal={signal || "NO SIGNAL"} />
          </Stack>

          <Stack spacing={0.8}>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}
            >
              <Typography variant="body2" color="text.secondary">
                Readiness
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {readiness ?? "N/A"}
              </Typography>
            </Box>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}
            >
              <Typography variant="body2" color="text.secondary">
                Relative Strength
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {formatValue(relativeStrength, 1)}
              </Typography>
            </Box>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}
            >
              <Typography variant="body2" color="text.secondary">
                RSI
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {formatValue(rsi, 1)}
              </Typography>
            </Box>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}
            >
              <Typography variant="body2" color="text.secondary">
                ATR
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {formatValue(atr, 1)}
              </Typography>
            </Box>
          </Stack>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 0.25, lineHeight: 1.6 }}
          >
            {explanation || "No opportunity explanation available."}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default OpportunityCard;

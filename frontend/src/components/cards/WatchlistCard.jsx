import { Box, Card, CardContent, Grid, Stack, Typography } from "@mui/material";
import PriorityChip from "../chips/PriorityChip";
import SignalChip from "../chips/SignalChip";

function WatchlistCard({
  symbol,
  priority,
  readiness,
  relativeStrength,
  rsi,
  signal,
  explanation,
}) {
  return (
    <Card sx={{ borderLeft: "1px solid rgba(255,255,255,0.08)" }}>
      <CardContent sx={{ p: 2 }}>
        <Stack spacing={1.25}>
          <Stack
            direction="row"
            spacing={1}
            sx={{ justifyContent: "space-between", alignItems: "center" }}
          >
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {symbol}
            </Typography>
            <SignalChip signal={signal} />
          </Stack>

          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Typography variant="body2" color="text.secondary">
              Priority
            </Typography>
            <PriorityChip priority={priority} />
          </Stack>

          <Grid container spacing={1}>
            <Grid size={{ xs: 6 }}>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  Readiness
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {readiness ?? "N/A"}
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  RS
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {Number(relativeStrength || 0).toFixed(1)}
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  RSI
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {Number(rsi || 0).toFixed(1)}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ lineHeight: 1.5 }}
          >
            {explanation || "No explanation provided."}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default WatchlistCard;

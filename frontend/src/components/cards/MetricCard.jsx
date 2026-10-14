import { Card, CardContent, Stack, Typography } from "@mui/material";

function MetricCard({ label, value, suffix = "", accent = "primary.main" }) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent sx={{ p: 2.5 }}>
        <Stack spacing={1.25}>
          <Typography
            variant="overline"
            color="text.secondary"
            sx={{ letterSpacing: 0.8 }}
          >
            {label}
          </Typography>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              lineHeight: 1.2,
              color: accent,
            }}
          >
            {value}
            {suffix}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default MetricCard;

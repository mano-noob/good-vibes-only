import { Card, CardContent, Chip, Stack, Typography } from "@mui/material";

function AlertCard({ title, message, severity = "medium", timestamp }) {
  const colorMap = {
    high: "error",
    critical: "error",
    medium: "warning",
    low: "success",
    info: "info",
  };

  const normalized = String(severity || "medium").toLowerCase();
  const color = colorMap[normalized] || "default";
  const timeLabel = timestamp
    ? new Date(timestamp).toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "Just now";

  return (
    <Card
      sx={{
        borderLeft: `4px solid ${color === "default" ? "primary.main" : `${color}.main`}`,
        background: "rgba(30,30,30,0.9)",
      }}
    >
      <CardContent sx={{ p: 2.25 }}>
        <Stack spacing={1}>
          <Chip
            label={normalized.toUpperCase()}
            color={color}
            size="small"
            sx={{ alignSelf: "flex-start" }}
          />
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ lineHeight: 1.6 }}
          >
            {message}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {timeLabel}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default AlertCard;

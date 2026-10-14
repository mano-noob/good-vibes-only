import { Card, CardContent, Stack, Typography } from "@mui/material";

function SummaryCard({ title, value, subtitle, color = "primary.main" }) {
  return (
    <Card
      sx={{
        height: "100%",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Stack spacing={1.25}>
          <Typography
            variant="overline"
            color="text.secondary"
            sx={{ letterSpacing: 0.8 }}
          >
            {title}
          </Typography>
          <Typography
            variant="h5"
            sx={{ color, fontWeight: 700, lineHeight: 1.2 }}
          >
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

export default SummaryCard;

import { Chip } from "@mui/material";

function StatusChip({ decision, ...props }) {
  const normalized = String(decision || "")
    .trim()
    .toUpperCase();

  const config = {
    HOLD: { label: "Holding", color: "success", variant: "filled" },
    EXIT: { label: "Exit Candidate", color: "error", variant: "filled" },
    BUY: { label: "Buy Candidate", color: "info", variant: "filled" },
    WATCHLIST: { label: "Watchlist", color: "default", variant: "outlined" },
  };

  const chip = config[normalized] || {
    label: normalized || "N/A",
    color: "default",
    variant: "filled",
  };

  return (
    <Chip
      {...props}
      label={chip.label}
      color={chip.color}
      variant={chip.variant}
      size="small"
      sx={{
        minWidth: 120,
        px: 0.5,
        ...props.sx,
      }}
    />
  );
}

export default StatusChip;

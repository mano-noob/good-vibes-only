import { Chip } from "@mui/material";

function SignalChip({ signal, ...props }) {
  const normalized = String(signal || "")
    .trim()
    .toUpperCase();

  const config = {
    BUY: { label: "BUY", color: "success", variant: "filled" },
    HOLD: { label: "HOLD", color: "info", variant: "filled" },
    WATCHLIST: { label: "WATCHLIST", color: "default", variant: "filled" },
    EXIT: { label: "EXIT", color: "error", variant: "filled" },
    "NO SIGNAL": { label: "NO SIGNAL", color: "warning", variant: "filled" },
  };

  const chip = config[normalized] || {
    label: normalized || "NO SIGNAL",
    color: "warning",
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
        minWidth: 96,
        px: 0.5,
        ...props.sx,
      }}
    />
  );
}

export default SignalChip;

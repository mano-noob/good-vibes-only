import { Chip } from "@mui/material";

function PriorityChip({ priority, ...props }) {
  const normalized = String(priority || "")
    .trim()
    .toUpperCase();

  const config = {
    A: { label: "A", color: "success", variant: "filled" },
    B: { label: "B", color: "info", variant: "filled" },
    C: { label: "C", color: "warning", variant: "filled" },
    D: { label: "D", color: "default", variant: "outlined" },
    IGNORE: { label: "Ignore", color: "default", variant: "filled" },
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
        minWidth: 66,
        px: 0.5,
        ...props.sx,
      }}
    />
  );
}

export default PriorityChip;

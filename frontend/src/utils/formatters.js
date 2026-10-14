export const safeNumber = (value, fallback = 0) => {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
};

export const formatMoney = (value) =>
  `₹${safeNumber(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

export const formatPercent = (value, digits = 2) =>
  `${safeNumber(value).toFixed(digits)}%`;

export const normalizePayload = (payload, fallback = {}) =>
  payload?.data?.data ?? payload?.data ?? fallback;

export const formatReviewDate = (dateValue) => {
  if (!dateValue) return "Unknown";

  const parsed = new Date(dateValue.replace(" ", "T"));

  if (Number.isNaN(parsed.getTime())) {
    return dateValue;
  }

  return parsed.toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

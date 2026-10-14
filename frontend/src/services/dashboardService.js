import { apiClient } from "../api/client";
import { normalizePayload } from "../utils/formatters";

export const getReview = async () => {
  const response = await apiClient.get("/trading/review");
  return normalizePayload(response, {});
};

export const getPortfolio = async () => {
  const response = await apiClient.get("/portfolio");
  return normalizePayload(response, { positions: [] });
};

export const getDashboardSummary = async () => {
  const [review, portfolio] = await Promise.all([getReview(), getPortfolio()]);
  return { review, portfolio };
};

export const dashboardService = {
  getReview,
  getPortfolio,
  getDashboardSummary,
};

export default dashboardService;

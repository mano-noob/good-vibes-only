import api, { apiClient } from "./client";

export const getReview = () => apiClient.get("/trading/review");
export const getHealth = () => apiClient.get("/system/health");
export const getMetrics = () => apiClient.get("/system/metrics");
export const getPortfolio = () => apiClient.get("/portfolio");
export const getPortfolioSummary = () => apiClient.get("/portfolio/summary");

export default api;

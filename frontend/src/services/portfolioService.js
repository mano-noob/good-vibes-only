import { apiClient } from "../api/client";
import { normalizePayload } from "../utils/formatters";

export const fetchPortfolio = async () => {
  const response = await apiClient.get("/portfolio");
  return normalizePayload(response, { positions: [] });
};

export default { fetchPortfolio };

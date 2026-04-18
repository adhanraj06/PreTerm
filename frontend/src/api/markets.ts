import { apiRequest } from "./client";
import type { Market, MarketDetail } from "../types/market";

export function getMarkets(): Promise<Market[]> {
  return apiRequest<Market[]>("/api/markets");
}

export function getMarket(marketId: number): Promise<MarketDetail> {
  return apiRequest<MarketDetail>(`/api/markets/${marketId}`);
}

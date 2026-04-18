import { apiRequest } from "./client";
import type { EdgarBrowseResult, FinanceContext } from "../types/finance";

export function getMarketFinanceContext(marketId: number): Promise<FinanceContext> {
  return apiRequest<FinanceContext>(`/api/markets/${marketId}/finance-context`);
}

export function getEdgarFilings(params: {
  ticker: string;
  forms?: string[];
  limit?: number;
}): Promise<EdgarBrowseResult> {
  const forms = (params.forms ?? ["10-K", "10-Q", "8-K"]).join(",");
  const limit = params.limit ?? 12;
  const q = new URLSearchParams({ ticker: params.ticker, forms, limit: String(limit) });
  return apiRequest<EdgarBrowseResult>(`/api/finance/edgar/filings?${q.toString()}`);
}

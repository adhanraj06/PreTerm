import { apiRequest } from "./client";
import type { HeadlineMapResult } from "./headlines";
import type { MarketDetail } from "../types/market";
import type { Watchlist } from "../types/watchlist";

type CopilotMarketContext = {
  id: number;
  title: string;
  category: string;
  status: string;
  last_price: number;
  probability_change: number;
  description: string | null;
  summary: string | null;
  why_this_matters_now: string | null;
  what_changed: string | null;
  bull_case: string | null;
  base_case: string | null;
  bear_case: string | null;
  catalysts: string | null;
  drivers: string | null;
  risks: string | null;
  what_would_change_probability: string | null;
};

export type CopilotChatRequest = {
  message: string;
  selected_market: CopilotMarketContext | null;
  pinned_markets: CopilotMarketContext[];
  watchlists: Array<{
    id: number;
    name: string;
    markets: CopilotMarketContext[];
  }>;
  recent_headline_map: {
    headline_text: string;
    top_match: HeadlineMapResult["top_match"];
    candidates: HeadlineMapResult["candidates"];
  } | null;
};

export type CopilotChatResponse = {
  response_text: string;
  source: "gemini" | "mock";
  references: Array<{
    label: string;
    type: string;
  }>;
};

export function buildCopilotMarketContext(market: MarketDetail | null): CopilotMarketContext | null {
  if (!market) {
    return null;
  }

  return {
    id: market.id,
    title: market.title,
    category: market.category,
    status: market.status,
    last_price: market.last_price,
    probability_change: market.probability_change,
    description: market.description,
    summary: market.brief?.summary ?? null,
    why_this_matters_now: market.brief?.why_this_matters_now ?? null,
    what_changed: market.brief?.what_changed ?? null,
    bull_case: market.brief?.bull_case ?? null,
    base_case: market.brief?.base_case ?? null,
    bear_case: market.brief?.bear_case ?? null,
    catalysts: market.brief?.catalysts ?? null,
    drivers: market.brief?.drivers ?? null,
    risks: market.brief?.risks ?? null,
    what_would_change_probability: market.brief?.what_would_change_probability ?? null,
  };
}

export function buildCopilotWatchlistContext(watchlists: Watchlist[]) {
  return watchlists.map((watchlist) => ({
    id: watchlist.id,
    name: watchlist.name,
    markets: watchlist.items.map((item) => ({
      id: item.market.id,
      title: item.market.title,
      category: item.market.category,
      status: item.market.status,
      last_price: item.market.last_price,
      probability_change: item.market.probability_change,
      description: null,
      summary: null,
      why_this_matters_now: null,
      what_changed: null,
      bull_case: null,
      base_case: null,
      bear_case: null,
      catalysts: null,
      drivers: null,
      risks: null,
      what_would_change_probability: null,
    })),
  }));
}

export function chatWithCopilot(
  token: string,
  payload: CopilotChatRequest,
): Promise<CopilotChatResponse> {
  return apiRequest<CopilotChatResponse>("/api/copilot/chat", {
    method: "POST",
    token,
    body: payload,
  });
}

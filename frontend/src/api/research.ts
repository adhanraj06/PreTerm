import { apiRequest } from "./client";
import type { AssetContext } from "../types/finance";
import type { MacroSeries } from "../types/macro";

export type MacroCatalogItem = { key: string; title: string };

export type ResearchQuoteResponse = {
  available: boolean;
  reason: string | null;
  asset: AssetContext | null;
};

export function getResearchMacroCatalog(): Promise<MacroCatalogItem[]> {
  return apiRequest<MacroCatalogItem[]>("/api/research/macro/catalog");
}

export function getResearchMacroSeries(seriesKey: string): Promise<MacroSeries> {
  return apiRequest<MacroSeries>(`/api/research/macro/${encodeURIComponent(seriesKey)}`);
}

export function getResearchQuote(ticker: string): Promise<ResearchQuoteResponse> {
  const q = new URLSearchParams({ ticker: ticker.trim() });
  return apiRequest<ResearchQuoteResponse>(`/api/research/quote?${q.toString()}`);
}

export type EquityNewsItem = {
  title: string;
  text: string;
  url: string | null;
  source: string | null;
  score?: number | null;
};

export type EquityNewsResponse = {
  items: EquityNewsItem[];
};

export function getResearchEquityNews(ticker: string, redditSubreddit = "stocks"): Promise<EquityNewsResponse> {
  const q = new URLSearchParams({
    ticker: ticker.trim(),
    reddit_subreddit: redditSubreddit.trim().replace(/^r\//i, "") || "stocks",
  });
  return apiRequest<EquityNewsResponse>(`/api/research/equity-news?${q.toString()}`);
}

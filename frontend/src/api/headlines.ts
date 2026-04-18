import { apiRequest } from "./client";

export type HeadlineMapCandidate = {
  market_id: number;
  title: string;
  category: string;
  match_strength: number;
  directional_impact: "bullish" | "bearish" | "mixed";
  explanation: string;
  why_it_matters: string;
};

export type HeadlineMapResult = {
  top_match: HeadlineMapCandidate | null;
  candidates: HeadlineMapCandidate[];
};

export function mapHeadline(headlineText: string): Promise<HeadlineMapResult> {
  return apiRequest<HeadlineMapResult>("/api/headline-map", {
    method: "POST",
    body: { headline_text: headlineText },
  });
}

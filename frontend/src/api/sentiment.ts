import { apiRequest } from "./client";
import type { HeadlineMapCandidate } from "./headlines";

export type SentimentResult = {
  source: string;
  source_label?: string;
  title_text: string;
  compound_score: number;
  sentiment_label: "bullish" | "bearish" | "neutral";
  matched_market: HeadlineMapCandidate | null;
  extraction_note: string | null;
};

export function analyzeSentimentText(payload: {
  text: string;
  source?: string;
  title?: string;
}): Promise<SentimentResult> {
  return apiRequest<SentimentResult>("/api/sentiment/analyze-text", {
    method: "POST",
    body: payload,
  });
}

export function analyzeSentimentUrl(url: string): Promise<SentimentResult> {
  return apiRequest<SentimentResult>("/api/sentiment/analyze-url", {
    method: "POST",
    body: { url },
  });
}

export function analyzeSentimentRedditHot(payload: {
  subreddit?: string;
  limit?: number;
}): Promise<SentimentResult> {
  return apiRequest<SentimentResult>("/api/sentiment/analyze-reddit-hot", {
    method: "POST",
    body: payload,
  });
}

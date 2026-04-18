import { apiRequest } from "./client";

export type NewsItem = {
  title: string;
  text: string;
  url: string | null;
  source: string | null;
  score?: number | null;
};

export type NewsFeedResponse = {
  items: NewsItem[];
};

export function fetchRedditNews(subreddit?: string, limit?: number): Promise<NewsFeedResponse> {
  const q = new URLSearchParams();
  if (subreddit) {
    q.set("subreddit", subreddit);
  }
  if (limit != null) {
    q.set("limit", String(limit));
  }
  const suffix = q.toString();
  return apiRequest<NewsFeedResponse>(`/api/news/reddit${suffix ? `?${suffix}` : ""}`);
}

export function fetchRssNews(feedKey: string, limit?: number): Promise<NewsFeedResponse> {
  const q = new URLSearchParams();
  if (limit != null) {
    q.set("limit", String(limit));
  }
  const suffix = q.toString();
  return apiRequest<NewsFeedResponse>(`/api/news/rss/${feedKey}${suffix ? `?${suffix}` : ""}`);
}

export function fetchNewsFeedIndex(): Promise<Record<string, string>> {
  return apiRequest<Record<string, string>>("/api/news/feeds");
}

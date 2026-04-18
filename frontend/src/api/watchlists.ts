import { apiRequest } from "./client";
import type { Watchlist } from "../types/watchlist";

export function getWatchlists(token: string): Promise<Watchlist[]> {
  return apiRequest<Watchlist[]>("/api/watchlists", { token });
}

export function createWatchlist(token: string, name: string): Promise<Watchlist> {
  return apiRequest<Watchlist>("/api/watchlists", {
    method: "POST",
    token,
    body: { name },
  });
}

export function deleteWatchlist(token: string, watchlistId: number): Promise<void> {
  return apiRequest<void>(`/api/watchlists/${watchlistId}`, {
    method: "DELETE",
    token,
  });
}

export function addWatchlistItem(
  token: string,
  watchlistId: number,
  marketId: number,
): Promise<Watchlist> {
  return apiRequest<Watchlist>(`/api/watchlists/${watchlistId}/items`, {
    method: "POST",
    token,
    body: { market_id: marketId },
  });
}

export function deleteWatchlistItem(
  token: string,
  watchlistId: number,
  itemId: number,
): Promise<Watchlist> {
  return apiRequest<Watchlist>(`/api/watchlists/${watchlistId}/items/${itemId}`, {
    method: "DELETE",
    token,
  });
}

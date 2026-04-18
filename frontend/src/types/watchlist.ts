export type WatchlistMarketSummary = {
  id: number;
  title: string;
  slug: string;
  category: string;
  status: string;
  last_price: number;
  probability_change: number;
};

export type WatchlistItem = {
  id: number;
  market_id: number;
  position: number | null;
  notes: string | null;
  created_at: string;
  market: WatchlistMarketSummary;
};

export type Watchlist = {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  items: WatchlistItem[];
};

export type SavedView = {
  id: number;
  name: string;
  layout_json: Record<string, unknown> | null;
  filters_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

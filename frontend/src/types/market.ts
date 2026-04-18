export type MarketBrief = {
  summary: string;
  why_this_matters_now: string;
  what_changed: string;
  bull_case: string;
  base_case: string;
  bear_case: string;
  catalysts: string;
  drivers: string;
  risks: string;
  what_would_change_probability: string;
  sources_json: Array<{ label: string; type: string }>;
  recent_headlines_json: Array<{
    title: string;
    source: string;
    published_at: string;
    why_it_matters: string;
  }>;
  generated_at: string;
};

export type MarketSnapshot = {
  id: number;
  captured_at: string;
  price: number;
  volume: number | null;
  open_interest: number | null;
  metadata_json: Record<string, unknown> | null;
};

export type MarketTimelineEntry = {
  id: number;
  occurred_at: string;
  move: number | null;
  price_after_move: number | null;
  reason: string;
  linked_label: string | null;
  linked_type: string | null;
  linked_url: string | null;
  metadata_json: Record<string, unknown> | null;
};

export type Market = {
  id: number;
  external_id: string | null;
  source: string;
  title: string;
  slug: string;
  category: string;
  status: string;
  close_time: string | null;
  last_price: number;
  probability_change: number;
  volume: number | null;
  open_interest: number | null;
  description: string | null;
  metadata_json: Record<string, unknown> | null;
  brief: MarketBrief | null;
};

export type MarketDetail = Market & {
  snapshots: MarketSnapshot[];
  timeline_entries: MarketTimelineEntry[];
};

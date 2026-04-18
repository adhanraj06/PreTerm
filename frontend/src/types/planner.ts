export type PlannedEventMarketSuggestion = {
  market: {
    id: number;
    title: string;
    slug: string;
    category: string;
    status: string;
    last_price: number;
    probability_change: number;
  };
  relevance_score: number;
  rationale: string;
};

export type PlannedEvent = {
  id: number;
  title: string;
  date: string;
  location: string | null;
  concern_type: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  suggestions: PlannedEventMarketSuggestion[];
};

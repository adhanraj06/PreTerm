export type MacroObservation = {
  date: string;
  value: number;
};

export type MacroSeries = {
  series_id: string;
  title: string;
  units: string;
  frequency: string;
  latest_value: number | null;
  previous_value: number | null;
  change: number | null;
  observations: MacroObservation[];
};

export type MacroContext = {
  available: boolean;
  reason: string | null;
  market_id: number;
  market_title: string;
  series: MacroSeries[];
  macro_source: string | null;
};

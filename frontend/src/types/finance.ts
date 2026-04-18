export type AssetObservation = {
  date: string;
  close: number;
};

export type AssetContext = {
  ticker: string;
  name: string;
  latest_price: number | null;
  price_change: number | null;
  currency: string | null;
  market_cap: number | null;
  exchange: string | null;
  observations: AssetObservation[];
};

export type EdgarFiling = {
  form: string;
  filing_date: string;
  description: string;
  document_url: string | null;
};

export type CompanyContext = {
  company_name: string;
  cik: string;
  latest_filings: EdgarFiling[];
};

export type FinanceContext = {
  available: boolean;
  reason: string | null;
  market_id: number;
  market_title: string;
  asset_context: AssetContext | null;
  company_context: CompanyContext | null;
  context_ticker: string | null;
  context_kind: string | null;
};

export type EdgarBrowseResult = {
  available: boolean;
  reason: string | null;
  ticker: string;
  company_name: string;
  cik: string;
  filings: EdgarFiling[];
};

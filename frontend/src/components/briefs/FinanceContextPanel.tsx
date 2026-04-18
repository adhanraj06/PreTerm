import { useCallback, useEffect, useState } from "react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getEdgarFilings } from "../../api/finance";
import type { EdgarFiling, FinanceContext } from "../../types/finance";

function formatPrice(value: number | null, currency: string | null) {
  if (value === null) {
    return "N/A";
  }
  return currency ? `${value.toFixed(2)} ${currency}` : value.toFixed(2);
}

function formatMarketCap(value: number | null) {
  if (value === null) {
    return "N/A";
  }
  if (value >= 1_000_000_000_000) {
    return `${(value / 1_000_000_000_000).toFixed(2)}T`;
  }
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  }
  return value.toLocaleString();
}

const FORM_OPTIONS = ["10-K", "10-Q", "8-K", "4", "DEF 14A"] as const;

function FilingsList({ filings }: { filings: EdgarFiling[] }) {
  return (
    <>
      {filings.map((filing) => (
        <div key={`${filing.form}-${filing.filing_date}`} className="headline-card">
          <strong>{filing.form}</strong>
          <small>{new Date(filing.filing_date).toLocaleDateString()}</small>
          <p>{filing.description}</p>
          {filing.document_url ? (
            <a href={filing.document_url} target="_blank" rel="noreferrer" className="inline-link">
              Open Filing
            </a>
          ) : null}
        </div>
      ))}
    </>
  );
}

export function FinanceContextPanel({ context }: { context: FinanceContext }) {
  const [filings, setFilings] = useState<EdgarFiling[]>(context.company_context?.latest_filings ?? []);
  const [selectedForms, setSelectedForms] = useState<string[]>(["10-K", "10-Q", "8-K"]);
  const [filingsLimit, setFilingsLimit] = useState(12);
  const [edgarBusy, setEdgarBusy] = useState(false);
  const [edgarError, setEdgarError] = useState<string | null>(null);

  useEffect(() => {
    setFilings(context.company_context?.latest_filings ?? []);
  }, [context.company_context]);

  const ticker = context.context_ticker ?? context.asset_context?.ticker ?? "";
  const showEdgarTools =
    context.context_kind === "company" && Boolean(ticker) && Boolean(context.company_context);

  const toggleForm = useCallback((form: string) => {
    setSelectedForms((prev) => (prev.includes(form) ? prev.filter((f) => f !== form) : [...prev, form]));
  }, []);

  const reloadFilings = useCallback(async () => {
    if (!ticker || selectedForms.length === 0) {
      setEdgarError("Pick at least one filing type.");
      return;
    }
    setEdgarBusy(true);
    setEdgarError(null);
    try {
      const res = await getEdgarFilings({ ticker, forms: selectedForms, limit: filingsLimit });
      if (!res.available) {
        setEdgarError(res.reason ?? "EDGAR request failed.");
        return;
      }
      setFilings(res.filings);
    } catch {
      setEdgarError("Could not reach the EDGAR endpoint.");
    } finally {
      setEdgarBusy(false);
    }
  }, [filingsLimit, selectedForms, ticker]);

  if (!context.available || (!context.asset_context && !context.company_context)) {
    return null;
  }

  return (
    <article className="brief-foot-card finance-context-card">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">Markets Desk</span>
          <h4>{context.asset_context?.name ?? context.company_context?.company_name}</h4>
          <small className="macro-source-hint">
            Yahoo Finance (yfinance)
            {context.company_context ? " · SEC EDGAR (edgartools)" : ""}
            {context.context_kind ? ` · ${context.context_kind}` : ""}
          </small>
        </div>
      </div>

      {context.asset_context ? (
        <div className="finance-asset-stack">
          <div className="detail-stats">
            <div>
              <span className="section-kicker">Ticker</span>
              <strong>{context.asset_context.ticker}</strong>
            </div>
            <div>
              <span className="section-kicker">Last Price</span>
              <strong>
                {formatPrice(context.asset_context.latest_price, context.asset_context.currency)}
              </strong>
            </div>
            <div>
              <span className="section-kicker">Move vs Prev</span>
              <strong>
                {context.asset_context.price_change !== null
                  ? `${context.asset_context.price_change >= 0 ? "+" : ""}${context.asset_context.price_change.toFixed(2)}`
                  : "N/A"}
              </strong>
            </div>
            <div>
              <span className="section-kicker">Market Cap</span>
              <strong>{formatMarketCap(context.asset_context.market_cap)}</strong>
            </div>
          </div>

          <div className="macro-mini-chart">
            <ResponsiveContainer width="100%" height={100}>
              <LineChart data={context.asset_context.observations}>
                <XAxis dataKey="date" hide />
                <YAxis hide domain={["dataMin", "dataMax"]} />
                <Tooltip
                  formatter={(value: number) =>
                    formatPrice(value, context.asset_context?.currency ?? null)
                  }
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                  contentStyle={{
                    background: "#0c1118",
                    border: "1px solid rgba(129, 154, 185, 0.18)",
                    borderRadius: "10px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#7fd8c8"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 3, fill: "#d8fff8" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : null}

      {context.company_context && filings.length > 0 ? (
        <div className="finance-filings-stack">
          <span className="section-kicker">SEC filings</span>
          {showEdgarTools ? (
            <div className="edgar-filing-controls">
              <div className="edgar-form-toggles">
                {FORM_OPTIONS.map((form) => (
                  <label key={form} className="edgar-form-chip">
                    <input
                      type="checkbox"
                      checked={selectedForms.includes(form)}
                      onChange={() => toggleForm(form)}
                    />
                    {form}
                  </label>
                ))}
              </div>
              <div className="edgar-fetch-row">
                <label className="edgar-limit">
                  Max
                  <input
                    type="number"
                    min={1}
                    max={40}
                    value={filingsLimit}
                    onChange={(e) => setFilingsLimit(Number(e.target.value) || 12)}
                  />
                </label>
                <button
                  type="button"
                  className="scenario-toggle"
                  disabled={edgarBusy}
                  onClick={() => void reloadFilings()}
                >
                  {edgarBusy ? "Loading…" : "Reload from EDGAR"}
                </button>
              </div>
              {edgarError ? <div className="form-error">{edgarError}</div> : null}
            </div>
          ) : null}
          <FilingsList filings={filings} />
        </div>
      ) : null}
    </article>
  );
}

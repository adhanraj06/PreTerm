import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getEdgarFilings } from "../../api/finance";
import {
  getResearchEquityNews,
  getResearchMacroCatalog,
  getResearchMacroSeries,
  getResearchQuote,
  type EquityNewsItem,
} from "../../api/research";
import type { EdgarBrowseResult } from "../../types/finance";
import type { MacroSeries } from "../../types/macro";

type DeskTab = "equities" | "macro";

export function ResearchPage() {
  const [tab, setTab] = useState<DeskTab>("equities");

  const [eqTicker, setEqTicker] = useState("AAPL");
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteError, setQuoteError] = useState<string | null>(null);
  const [quote, setQuote] = useState<Awaited<ReturnType<typeof getResearchQuote>> | null>(null);
  const [equityRedditSub, setEquityRedditSub] = useState("stocks");
  const [equityNews, setEquityNews] = useState<EquityNewsItem[]>([]);
  const [equityNewsLoading, setEquityNewsLoading] = useState(false);
  const [equityNewsError, setEquityNewsError] = useState<string | null>(null);

  const [edgarLoading, setEdgarLoading] = useState(false);
  const [edgarError, setEdgarError] = useState<string | null>(null);
  const [edgar, setEdgar] = useState<EdgarBrowseResult | null>(null);

  const [macroCatalog, setMacroCatalog] = useState<{ key: string; title: string }[]>([]);
  const [macroKey, setMacroKey] = useState("cpi");
  const [macroLoading, setMacroLoading] = useState(false);
  const [macroError, setMacroError] = useState<string | null>(null);
  const [macroSeries, setMacroSeries] = useState<MacroSeries | null>(null);

  useEffect(() => {
    let on = true;
    void (async () => {
      try {
        const rows = await getResearchMacroCatalog();
        if (on) {
          setMacroCatalog(rows);
        }
      } catch {
        if (on) {
          setMacroCatalog([]);
        }
      }
    })();
    return () => {
      on = false;
    };
  }, []);

  useEffect(() => {
    if (macroCatalog.length === 0) {
      return;
    }
    if (!macroCatalog.some((row) => row.key === macroKey)) {
      setMacroKey(macroCatalog[0].key);
    }
  }, [macroCatalog, macroKey]);

  async function loadEquityNews(sym: string) {
    setEquityNewsError(null);
    setEquityNewsLoading(true);
    try {
      const res = await getResearchEquityNews(sym, equityRedditSub);
      setEquityNews(res.items);
    } catch (e) {
      setEquityNewsError(e instanceof Error ? e.message : "News request failed.");
      setEquityNews([]);
    } finally {
      setEquityNewsLoading(false);
    }
  }

  async function runQuote() {
    setQuoteError(null);
    setQuoteLoading(true);
    setEquityNews([]);
    try {
      const res = await getResearchQuote(eqTicker);
      setQuote(res);
      if (!res.available) {
        setQuoteError(res.reason ?? "Unavailable.");
      } else {
        void loadEquityNews(eqTicker.trim());
      }
    } catch (e) {
      setQuoteError(e instanceof Error ? e.message : "Request failed.");
      setQuote(null);
    } finally {
      setQuoteLoading(false);
    }
  }

  async function runEdgar() {
    const sym = eqTicker.trim().toUpperCase();
    if (!sym) {
      setEdgarError("Enter a ticker first.");
      return;
    }
    setEdgarError(null);
    setEdgarLoading(true);
    try {
      const res = await getEdgarFilings({ ticker: sym, limit: 20 });
      setEdgar(res);
      if (!res.available) {
        setEdgarError(res.reason ?? "EDGAR unavailable.");
      }
    } catch (e) {
      setEdgarError(e instanceof Error ? e.message : "Request failed.");
      setEdgar(null);
    } finally {
      setEdgarLoading(false);
    }
  }

  async function runMacro() {
    setMacroError(null);
    setMacroLoading(true);
    try {
      const s = await getResearchMacroSeries(macroKey);
      setMacroSeries(s);
    } catch (e) {
      setMacroError(e instanceof Error ? e.message : "Request failed.");
      setMacroSeries(null);
    } finally {
      setMacroLoading(false);
    }
  }

  useEffect(() => {
    if (tab !== "macro" || macroCatalog.length === 0) {
      return;
    }
    void runMacro();
    // Intentionally omit runMacro from deps: macroKey/tab/catalog gate the refresh.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, macroKey, macroCatalog.length]);

  return (
    <div className="surface-stack research-page">
      <section className="hero-panel compact">
        <div>
          <span className="section-kicker">Research</span>
          <h3>Equities (quotes, headlines, SEC) and macro</h3>
          <p className="hero-lead">
            Standalone desk: Yahoo Finance daily closes, EDGAR 10-K / 10-Q / 8-K links under the same ticker, and FRED
            (API or bundled CSV) time series. No contract context required.
          </p>
        </div>
      </section>

      <div className="scenario-toggle-strip">
        <button
          type="button"
          className={tab === "equities" ? "scenario-toggle active scenario-base" : "scenario-toggle"}
          onClick={() => setTab("equities")}
        >
          Equities
        </button>
        <button
          type="button"
          className={tab === "macro" ? "scenario-toggle active scenario-base" : "scenario-toggle"}
          onClick={() => setTab("macro")}
        >
          Macro (FRED)
        </button>
      </div>

      {tab === "equities" ? (
        <section className="research-panel">
          <div className="research-controls">
            <label className="field inline-field">
              <span>Ticker</span>
              <input value={eqTicker} onChange={(e) => setEqTicker(e.target.value.toUpperCase())} placeholder="AAPL" />
            </label>
            <label className="field inline-field">
              <span>Reddit sub (server fetch)</span>
              <input
                value={equityRedditSub}
                onChange={(e) => setEquityRedditSub(e.target.value.replace(/^r\//i, "").toLowerCase())}
                placeholder="stocks"
              />
            </label>
            <button type="button" className="primary-button" onClick={() => void runQuote()} disabled={quoteLoading}>
              {quoteLoading ? "Loading…" : "Load quote & news"}
            </button>
            <button type="button" className="ghost-button" onClick={() => void runEdgar()} disabled={edgarLoading}>
              {edgarLoading ? "EDGAR…" : "Load SEC filings"}
            </button>
            {quote?.available ? (
              <button
                type="button"
                className="ghost-button"
                onClick={() => void loadEquityNews(eqTicker.trim())}
                disabled={equityNewsLoading}
              >
                {equityNewsLoading ? "News…" : "Refresh news only"}
              </button>
            ) : null}
          </div>
          <p className="inline-note">
            Headlines use Google News RSS plus Reddit hot fetched through the API (avoids browser CORS on reddit.com).
          </p>
          {quoteError ? <div className="form-error">{quoteError}</div> : null}
          {edgarError ? <div className="form-error">{edgarError}</div> : null}
          {equityNewsError ? <div className="form-error">{equityNewsError}</div> : null}
          {quote?.available && quote.asset ? (
            <div className="research-grid">
              <article className="brief-foot-card">
                <span className="section-kicker">Quote</span>
                <h4>{quote.asset.name}</h4>
                <p className="research-stat-row">
                  <strong>{quote.asset.ticker}</strong>
                  {quote.asset.latest_price != null ? (
                    <span>
                      Last: {quote.asset.latest_price.toFixed(2)} {quote.asset.currency ?? ""}
                    </span>
                  ) : null}
                  {quote.asset.exchange ? <span>{quote.asset.exchange}</span> : null}
                </p>
              </article>
              <article className="brief-foot-card research-chart-card">
                <span className="section-kicker">Recent daily closes</span>
                {quote.asset.observations.length === 0 ? (
                  <div className="empty-state">No history returned.</div>
                ) : (
                  <div className="macro-mini-chart research-line-tall">
                    <ResponsiveContainer width="100%" height={280}>
                      <LineChart data={quote.asset.observations}>
                        <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                        <YAxis domain={["auto", "auto"]} width={56} tick={{ fontSize: 10 }} />
                        <Tooltip
                          labelFormatter={(l) => new Date(l).toLocaleDateString()}
                          formatter={(v: number) => [v.toFixed(2), "Close"]}
                          contentStyle={{
                            background: "#0c1118",
                            border: "1px solid rgba(129, 154, 185, 0.18)",
                            borderRadius: "10px",
                          }}
                        />
                        <Line type="monotone" dataKey="close" stroke="#7de2d1" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </article>
            </div>
          ) : null}
          {quote?.available && quote.asset ? (
            <article className="brief-foot-card research-news-card">
              <span className="section-kicker">Recent headlines</span>
              {equityNewsLoading && equityNews.length === 0 ? (
                <div className="inline-note">Loading headlines…</div>
              ) : equityNews.length === 0 ? (
                <div className="empty-state">No headlines yet. Load quote or refresh news.</div>
              ) : (
                <ul className="research-news-list">
                  {equityNews.map((item) => (
                    <li key={`${item.source}-${item.title}`}>
                      {item.url ? (
                        <a href={item.url} target="_blank" rel="noreferrer">
                          {item.title}
                        </a>
                      ) : (
                        <strong>{item.title}</strong>
                      )}
                      <div className="research-news-meta">
                        <span>{item.source ?? "News"}</span>
                        {item.score != null ? <span>score {item.score}</span> : null}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          ) : null}
          {edgar?.available ? (
            <article className="brief-foot-card">
              <span className="section-kicker">SEC filings (EDGAR)</span>
              <h4>
                {edgar.company_name} <small>(CIK {edgar.cik})</small>
              </h4>
              <ul className="research-filing-list">
                {edgar.filings.map((f) => (
                  <li key={`${f.form}-${f.filing_date}-${f.description}`}>
                    <strong>{f.form}</strong> · {f.filing_date}
                    {f.document_url ? (
                      <>
                        {" "}
                        <a href={f.document_url} target="_blank" rel="noreferrer">
                          Open filing
                        </a>
                      </>
                    ) : null}
                    <div className="filing-desc">{f.description}</div>
                  </li>
                ))}
              </ul>
            </article>
          ) : null}
        </section>
      ) : null}

      {tab === "macro" ? (
        <section className="research-panel">
          <div className="research-controls">
            <label className="field inline-field">
              <span>Series</span>
              <select value={macroKey} onChange={(e) => setMacroKey(e.target.value)}>
                {macroCatalog.map((row) => (
                  <option key={row.key} value={row.key}>
                    {row.title} ({row.key})
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="ghost-button" onClick={() => void runMacro()} disabled={macroLoading}>
              Refresh
            </button>
          </div>
          {macroLoading && !macroSeries ? <div className="inline-note">Loading series…</div> : null}
          {macroError ? <div className="form-error">{macroError}</div> : null}
          {macroSeries ? (
            <article className="brief-foot-card">
              <div className="panel-heading">
                <div>
                  <span className="section-kicker">FRED</span>
                  <h4>{macroSeries.title}</h4>
                  <small>
                    {macroSeries.series_id} · {macroSeries.frequency} · {macroSeries.units}
                  </small>
                </div>
                <div className="macro-series-metric">
                  <strong>
                    Latest:{" "}
                    {macroSeries.latest_value != null ? macroSeries.latest_value.toFixed(3) : "—"} {macroSeries.units}
                  </strong>
                </div>
              </div>
              <div className="macro-mini-chart research-line-tall">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={macroSeries.observations}>
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                    <YAxis domain={["auto", "auto"]} width={48} tick={{ fontSize: 10 }} />
                    <Tooltip
                      labelFormatter={(l) => new Date(l).toLocaleDateString()}
                      formatter={(v: number) => [`${v}`, macroSeries.units]}
                      contentStyle={{
                        background: "#0c1118",
                        border: "1px solid rgba(129, 154, 185, 0.18)",
                        borderRadius: "10px",
                      }}
                    />
                    <Line type="monotone" dataKey="value" stroke="#8cb4ff" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

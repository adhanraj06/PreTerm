import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getMarket, getMarkets } from "../../api/markets";
import { addWatchlistItem, getWatchlists } from "../../api/watchlists";
import { EventBriefPanel } from "../../components/briefs/EventBriefPanel";
import { MarketMoveChart } from "../../components/charts/MarketMoveChart";
import {
  applySmartMonitorOrder,
  getSmartRankingPreference,
  recordMarketViewed,
  setSmartRankingPreference,
} from "../../lib/deskRanking";
import type { Market, MarketDetail } from "../../types/market";
import type { Watchlist } from "../../types/watchlist";
import { useAuth } from "../auth/useAuth";
import { useMonitor } from "./MonitorContext";

type DataState = "idle" | "loading" | "error";

const deskModes = ["overview", "focused", "event"] as const;

const deskModeCopy: Record<(typeof deskModes)[number], { label: string; hint: string }> = {
  overview: {
    label: "All",
    hint: "Every contract matching your filters.",
  },
  focused: {
    label: "Pinned",
    hint: "Only markets you pinned on this desk.",
  },
  event: {
    label: "Closing",
    hint: "Soonest resolution dates first.",
  },
};

export function MonitorPage() {
  const { marketId: marketIdParam } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const {
    config,
    setDeskMode,
    setCategoryFilter,
    setSearchQuery,
    setSelectedMarketId,
    togglePinnedMarket,
  } = useMonitor();

  const detailMarketId = marketIdParam ? Number.parseInt(marketIdParam, 10) : NaN;
  const isDetailRoute = Number.isFinite(detailMarketId) && detailMarketId > 0;

  const [markets, setMarkets] = useState<Market[]>([]);
  const [marketDetail, setMarketDetail] = useState<MarketDetail | null>(null);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [dataState, setDataState] = useState<DataState>("loading");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [detailLoad, setDetailLoad] = useState<"idle" | "loading" | "error">("idle");
  const [smartOrder, setSmartOrder] = useState(() => getSmartRankingPreference());

  useEffect(() => {
    setSmartRankingPreference(smartOrder);
  }, [smartOrder]);

  useEffect(() => {
    if (isDetailRoute) {
      setSelectedMarketId(detailMarketId);
    }
  }, [detailMarketId, isDetailRoute, setSelectedMarketId]);

  useEffect(() => {
    let active = true;

    async function load() {
      setDataState("loading");
      try {
        const [marketData, watchlistData] = await Promise.all([
          getMarkets(),
          token ? getWatchlists(token) : Promise.resolve([]),
        ]);

        if (!active) {
          return;
        }

        setMarkets(marketData);
        setWatchlists(watchlistData);
        setDataState("idle");
      } catch {
        if (!active) {
          return;
        }
        setDataState("error");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token]);

  useEffect(() => {
    if (!isDetailRoute) {
      setMarketDetail(null);
      setDetailLoad("idle");
      return;
    }

    let active = true;
    setDetailLoad("loading");

    async function loadDetail() {
      try {
        const detail = await getMarket(detailMarketId);
        if (!active) {
          return;
        }
        setMarketDetail(detail);
        setDetailLoad("idle");
        recordMarketViewed(detailMarketId);
      } catch {
        if (!active) {
          return;
        }
        setMarketDetail(null);
        setDetailLoad("error");
      }
    }

    void loadDetail();

    return () => {
      active = false;
    };
  }, [detailMarketId, isDetailRoute]);

  const categories = useMemo(
    () => ["all", ...new Set(markets.map((market) => market.category))],
    [markets],
  );

  const watchlistMarketIds = useMemo(() => {
    const ids = new Set<number>();
    for (const list of watchlists) {
      for (const row of list.items) {
        ids.add(row.market_id);
      }
    }
    return ids;
  }, [watchlists]);

  const filteredMarkets = useMemo(() => {
    let rows = markets.filter((market) => {
      const categoryMatch =
        config.categoryFilter === "all" || market.category === config.categoryFilter;
      const query = config.searchQuery.toLowerCase().trim();
      const textMatch =
        query.length === 0 ||
        market.title.toLowerCase().includes(query) ||
        market.category.toLowerCase().includes(query);
      return categoryMatch && textMatch;
    });

    if (config.deskMode === "focused") {
      rows = rows.filter((m) => config.pinnedMarketIds.includes(m.id));
    }

    if (config.deskMode === "event") {
      rows = [...rows].sort((a, b) => {
        const ta = a.close_time ? new Date(a.close_time).getTime() : Number.MAX_SAFE_INTEGER;
        const tb = b.close_time ? new Date(b.close_time).getTime() : Number.MAX_SAFE_INTEGER;
        return ta - tb;
      });
    } else if (smartOrder) {
      rows = applySmartMonitorOrder(rows, watchlistMarketIds, config.pinnedMarketIds);
    }

    return rows;
  }, [
    config.categoryFilter,
    config.deskMode,
    config.pinnedMarketIds,
    config.searchQuery,
    markets,
    smartOrder,
    watchlistMarketIds,
  ]);

  async function handleAddToWatchlist(watchlistId: number, marketId: number) {
    if (!token) {
      return;
    }

    try {
      const updatedWatchlist = await addWatchlistItem(token, watchlistId, marketId);
      setWatchlists((current) =>
        current.map((watchlist) => (watchlist.id === updatedWatchlist.id ? updatedWatchlist : watchlist)),
      );
      const listName = updatedWatchlist.name;
      const marketName = markets.find((market) => market.id === marketId)?.title ?? "Market";
      setActionMessage(`${marketName} added to ${listName}.`);
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : "Unable to update watchlist.");
    }
  }

  if (isDetailRoute) {
    return (
      <div className="surface-stack monitor-detail-page">
        <button type="button" className="back-to-monitor" onClick={() => navigate("/app/monitor")}>
          ← All markets
        </button>

        {detailLoad === "error" ? (
          <div className="empty-state panel-pad">
            This market could not be loaded. It may have been removed from the feed.
          </div>
        ) : null}

        {detailLoad === "loading" || (!marketDetail && detailLoad === "idle") ? (
          <div className="empty-state panel-pad">Loading contract…</div>
        ) : null}

        {marketDetail ? (
          <>
            <header className="market-detail-header">
              <div className="market-detail-header-text">
                <span className="section-kicker">Contract</span>
                <h3>{marketDetail.title}</h3>
                <p className="detail-description">{marketDetail.description}</p>
              </div>
              <div className="market-detail-header-stats">
                <div>
                  <span className="section-kicker">Implied</span>
                  <strong>{Math.round(marketDetail.last_price * 100)}%</strong>
                </div>
                <div>
                  <span className="section-kicker">Move</span>
                  <strong className={marketDetail.probability_change >= 0 ? "delta positive" : "delta negative"}>
                    {marketDetail.probability_change >= 0 ? "+" : ""}
                    {Math.round(marketDetail.probability_change * 100)} pts
                  </strong>
                </div>
                <div>
                  <span className="section-kicker">Volume</span>
                  <strong>{marketDetail.volume?.toLocaleString() ?? "—"}</strong>
                </div>
                <span className="badge">{marketDetail.category}</span>
              </div>
            </header>

            <div className="market-detail-actions">
              <button
                type="button"
                className={
                  config.pinnedMarketIds.includes(marketDetail.id) ? "ghost-button active" : "ghost-button"
                }
                onClick={() => togglePinnedMarket(marketDetail.id)}
              >
                {config.pinnedMarketIds.includes(marketDetail.id) ? "Pinned" : "Pin to desk"}
              </button>
              {watchlists[0] ? (
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => void handleAddToWatchlist(watchlists[0].id, marketDetail.id)}
                >
                  Add to {watchlists[0].name}
                </button>
              ) : (
                <span className="inline-note">Create a watchlist to save this contract.</span>
              )}
            </div>

            <section className="market-detail-chart-card">
              <div className="panel-heading market-detail-chart-heading">
                <div>
                  <span className="section-kicker">Price history</span>
                  <h4>Implied probability over recent sessions</h4>
                </div>
              </div>
              <MarketMoveChart market={marketDetail} />
            </section>

            <EventBriefPanel market={marketDetail} showStandaloneChart />
          </>
        ) : null}
      </div>
    );
  }

  return (
    <div className="surface-stack monitor-list-page">
      <section className="hero-panel compact monitor-hero">
        <div>
          <span className="section-kicker">Monitor</span>
          <h3>Live contracts</h3>
          <p className="hero-lead">
            Open any row for a full-page view with chart, timeline, and research panels. Pin contracts to
            narrow your desk.
          </p>
        </div>
      </section>

      <section className="monitor-toolbar">
        <label className="field monitor-view-field">
          <span>View</span>
          <select
            className="monitor-view-select"
            aria-label="Desk view"
            value={config.deskMode}
            onChange={(event) => setDeskMode(event.target.value as (typeof deskModes)[number])}
          >
            {deskModes.map((mode) => (
              <option key={mode} value={mode}>
                {deskModeCopy[mode].label} — {deskModeCopy[mode].hint}
              </option>
            ))}
          </select>
        </label>

        <label
          className={`monitor-smart-inline${config.deskMode === "event" ? " monitor-smart-inline--disabled" : ""}`}
        >
          <input
            type="checkbox"
            checked={smartOrder}
            onChange={(event) => setSmartOrder(event.target.checked)}
            disabled={config.deskMode === "event"}
          />
          <span>Smart sort (recency &amp; watchlists, this browser only)</span>
        </label>

        <label className="field inline-field">
          <span>Category</span>
          <select value={config.categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>

        <label className="field inline-field monitor-search">
          <span>Search</span>
          <input
            type="search"
            value={config.searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Title or category"
          />
        </label>
      </section>

      {actionMessage ? <div className="flash-message">{actionMessage}</div> : null}

      <section className="monitor-list-section">
        <div className="panel-heading monitor-list-heading">
          <div>
            <span className="section-kicker">Universe</span>
            <h4>
              {filteredMarkets.length} contract{filteredMarkets.length === 1 ? "" : "s"}
            </h4>
          </div>
        </div>

        {dataState === "error" ? <div className="empty-state">Unable to load markets.</div> : null}

        {config.deskMode === "focused" && config.pinnedMarketIds.length === 0 ? (
          <div className="empty-state panel-pad">
            Nothing pinned yet. Use <strong>Pin</strong> on a contract (open it first) to build a focused list.
          </div>
        ) : null}

        <div className="market-card-grid">
          {filteredMarkets.map((market) => {
            const isPinned = config.pinnedMarketIds.includes(market.id);
            const primaryWatchlistId = watchlists[0]?.id;
            const pct = Math.round(market.last_price * 100);
            return (
              <article key={market.id} className="market-card">
                <button
                  type="button"
                  className="market-card-open"
                  onClick={() => navigate(`/app/monitor/${market.id}`)}
                >
                  <div className="market-card-top">
                    <h4 className="market-card-title">{market.title}</h4>
                    <div className="market-card-meta">
                      <span className="market-card-category">{market.category}</span>
                      <span className="market-card-status">{market.status}</span>
                    </div>
                  </div>
                  <div className="market-card-meter" aria-hidden>
                    <div className="market-card-meter-fill" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="market-card-stats">
                    <span className="market-card-pct">{pct}%</span>
                    <span
                      className={
                        market.probability_change >= 0 ? "delta positive market-card-delta" : "delta negative market-card-delta"
                      }
                    >
                      {market.probability_change >= 0 ? "+" : ""}
                      {Math.round(market.probability_change * 100)} pts
                    </span>
                  </div>
                </button>
                <div className="market-card-actions">
                  <button
                    type="button"
                    className={isPinned ? "mini-button active" : "mini-button"}
                    onClick={() => togglePinnedMarket(market.id)}
                  >
                    {isPinned ? "Pinned" : "Pin"}
                  </button>
                  <button
                    type="button"
                    className="mini-button"
                    disabled={!primaryWatchlistId}
                    onClick={() => {
                      if (primaryWatchlistId) {
                        void handleAddToWatchlist(primaryWatchlistId, market.id);
                      }
                    }}
                  >
                    Watchlist
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getMarkets } from "../../api/markets";
import { createSavedView, deleteSavedView, getSavedViews } from "../../api/views";
import {
  addWatchlistItem,
  createWatchlist,
  deleteWatchlist,
  deleteWatchlistItem,
  getWatchlists,
} from "../../api/watchlists";
import type { Market } from "../../types/market";
import type { SavedView, Watchlist } from "../../types/watchlist";
import { useAuth } from "../auth/useAuth";
import { useMonitor } from "../monitor/MonitorContext";

export function WatchlistsPage() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { config, createSavedViewPayload, applySavedView } = useMonitor();
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);
  const [markets, setMarkets] = useState<Market[]>([]);
  const [watchlistName, setWatchlistName] = useState("");
  const [savedViewName, setSavedViewName] = useState("");
  const [targetWatchlistId, setTargetWatchlistId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    const authToken = token;

    let active = true;

    async function load() {
      try {
        const [watchlistData, savedViewData, marketData] = await Promise.all([
          getWatchlists(authToken),
          getSavedViews(authToken),
          getMarkets(),
        ]);
        if (!active) {
          return;
        }
        setWatchlists(watchlistData);
        setSavedViews(savedViewData);
        setMarkets(marketData);
        setTargetWatchlistId(watchlistData[0]?.id ?? null);
      } catch (error) {
        if (!active) {
          return;
        }
        setStatusMessage(error instanceof Error ? error.message : "Unable to load persistence data.");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token]);

  const selectedMarket = useMemo(
    () => markets.find((market) => market.id === config.selectedMarketId) ?? null,
    [config.selectedMarketId, markets],
  );

  const pinnedMarkets = useMemo(
    () => markets.filter((market) => config.pinnedMarketIds.includes(market.id)),
    [config.pinnedMarketIds, markets],
  );

  async function handleCreateWatchlist(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !watchlistName.trim()) {
      return;
    }
    try {
      const watchlist = await createWatchlist(token, watchlistName);
      setWatchlists((current) => [watchlist, ...current]);
      setTargetWatchlistId(watchlist.id);
      setWatchlistName("");
      setStatusMessage(`Created watchlist: ${watchlist.name}`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to create watchlist.");
    }
  }

  async function handleAddCurrentSelection() {
    if (!token || !targetWatchlistId || !selectedMarket) {
      return;
    }
    try {
      const updated = await addWatchlistItem(token, targetWatchlistId, selectedMarket.id);
      setWatchlists((current) => current.map((entry) => (entry.id === updated.id ? updated : entry)));
      setStatusMessage(`Added ${selectedMarket.title} to ${updated.name}.`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to add selected market.");
    }
  }

  async function handleAddPinnedMarkets() {
    if (!token || !targetWatchlistId || pinnedMarkets.length === 0) {
      return;
    }

    try {
      let updatedWatchlist: Watchlist | null = null;
      for (const market of pinnedMarkets) {
        updatedWatchlist = await addWatchlistItem(token, targetWatchlistId, market.id);
      }
      if (updatedWatchlist) {
        setWatchlists((current) =>
          current.map((entry) => (entry.id === updatedWatchlist?.id ? updatedWatchlist : entry)),
        );
        setStatusMessage(`Added ${pinnedMarkets.length} pinned markets to ${updatedWatchlist.name}.`);
      }
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to add pinned markets.");
    }
  }

  async function handleSaveView(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !savedViewName.trim()) {
      return;
    }
    try {
      const savedView = await createSavedView(token, {
        name: savedViewName,
        ...createSavedViewPayload(),
      });
      setSavedViews((current) => [savedView, ...current]);
      setSavedViewName("");
      setStatusMessage(`Saved current monitor configuration as "${savedView.name}".`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to save current view.");
    }
  }

  function handleOpenSavedView(view: SavedView) {
    const layout = view.layout_json ?? {};
    const filters = view.filters_json ?? {};
    const selectedId = typeof layout.selectedMarketId === "number" ? layout.selectedMarketId : null;
    applySavedView({
      deskMode:
        filters.deskMode === "focused" || filters.deskMode === "event" ? filters.deskMode : "overview",
      categoryFilter: typeof filters.categoryFilter === "string" ? filters.categoryFilter : "all",
      searchQuery: typeof filters.searchQuery === "string" ? filters.searchQuery : "",
      selectedMarketId: selectedId,
      pinnedMarketIds: Array.isArray(layout.pinnedMarketIds)
        ? layout.pinnedMarketIds.filter((id): id is number => typeof id === "number")
        : [],
    });
    navigate(selectedId ? `/app/monitor/${selectedId}` : "/app/monitor");
  }

  async function handleDeleteWatchlist(watchlistId: number) {
    if (!token) {
      return;
    }
    try {
      await deleteWatchlist(token, watchlistId);
      setWatchlists((current) => current.filter((entry) => entry.id !== watchlistId));
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to delete watchlist.");
    }
  }

  async function handleRemoveWatchlistItem(watchlistId: number, itemId: number) {
    if (!token) {
      return;
    }
    try {
      const updated = await deleteWatchlistItem(token, watchlistId, itemId);
      setWatchlists((current) => current.map((entry) => (entry.id === updated.id ? updated : entry)));
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to remove market.");
    }
  }

  async function handleDeleteSavedView(savedViewId: number) {
    if (!token) {
      return;
    }
    try {
      await deleteSavedView(token, savedViewId);
      setSavedViews((current) => current.filter((entry) => entry.id !== savedViewId));
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to delete saved view.");
    }
  }

  function getSavedViewDeskMode(view: SavedView): string {
    return typeof view.filters_json?.deskMode === "string" ? view.filters_json.deskMode : "overview";
  }

  function getSavedViewPinnedCount(view: SavedView): number {
    const pinned = view.layout_json?.pinnedMarketIds;
    return Array.isArray(pinned) ? pinned.length : 0;
  }

  return (
    <div className="surface-stack">
      <section className="hero-panel compact">
        <div>
          <span className="section-kicker">Persistence Layer</span>
          <h3>Watchlists and saved views now personalize the desk.</h3>
          <p>
            Capture a monitor configuration, reopen it later, and keep selected or pinned contracts
            attached to named watchlists.
          </p>
        </div>
      </section>

      {statusMessage ? <div className="flash-message">{statusMessage}</div> : null}

      <section className="two-up-grid">
        <article className="product-card">
          <span className="section-kicker">Create Watchlist</span>
          <h4>Named market baskets</h4>
          <form className="auth-form" onSubmit={handleCreateWatchlist}>
            <label className="field">
              <span>Watchlist Name</span>
              <input
                type="text"
                value={watchlistName}
                onChange={(event) => setWatchlistName(event.target.value)}
                placeholder="Macro Rotation Desk"
              />
            </label>
            <button type="submit" className="primary-button">
              Create Watchlist
            </button>
          </form>
        </article>

        <article className="product-card">
          <span className="section-kicker">Save Current View</span>
          <h4>Persist monitor state</h4>
          <form className="auth-form" onSubmit={handleSaveView}>
            <label className="field">
              <span>Saved View Name</span>
              <input
                type="text"
                value={savedViewName}
                onChange={(event) => setSavedViewName(event.target.value)}
                placeholder="Rates Focused Morning View"
              />
            </label>
            <button type="submit" className="primary-button">
              Save Current Monitor Configuration
            </button>
          </form>
        </article>
      </section>

      <section className="two-up-grid">
        <article className="product-card">
          <span className="section-kicker">Quick Add</span>
          <h4>Current desk selection</h4>
          <label className="field">
            <span>Target Watchlist</span>
            <select
              value={targetWatchlistId ?? ""}
              onChange={(event) =>
                setTargetWatchlistId(event.target.value ? Number(event.target.value) : null)
              }
            >
              <option value="">Select watchlist</option>
              {watchlists.map((watchlist) => (
                <option key={watchlist.id} value={watchlist.id}>
                  {watchlist.name}
                </option>
              ))}
            </select>
          </label>

          <div className="quick-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={() => void handleAddCurrentSelection()}
              disabled={!selectedMarket || !targetWatchlistId}
            >
              Add Selected Market
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => void handleAddPinnedMarkets()}
              disabled={pinnedMarkets.length === 0 || !targetWatchlistId}
            >
              Add Pinned Markets ({pinnedMarkets.length})
            </button>
          </div>

          <ul className="meta-list">
            <li>Desk mode: {config.deskMode}</li>
            <li>Category filter: {config.categoryFilter}</li>
            <li>Search query: {config.searchQuery || "None"}</li>
            <li>Selected market: {selectedMarket?.title ?? "None"}</li>
          </ul>
        </article>

        <article className="product-card">
          <span className="section-kicker">Pinned Desk</span>
          <h4>Currently pinned markets</h4>
          {pinnedMarkets.length === 0 ? (
            <div className="empty-state">Pin markets from the monitor to surface them here.</div>
          ) : (
            <div className="stacked-cards compact-stack">
              {pinnedMarkets.map((market) => (
                <div key={market.id} className="mini-market-card">
                  <strong>{market.title}</strong>
                  <small>
                    {market.category} · {Math.round(market.last_price * 100)}%
                  </small>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>

      <section className="two-up-grid">
        <article className="product-card">
          <span className="section-kicker">Watchlists</span>
          <h4>{watchlists.length} saved watchlists</h4>
          <div className="stacked-cards compact-stack">
            {watchlists.map((watchlist) => (
              <div key={watchlist.id} className="list-card">
                <div className="list-card-header">
                  <div>
                    <strong>{watchlist.name}</strong>
                    <small>{watchlist.items.length} markets</small>
                  </div>
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={() => void handleDeleteWatchlist(watchlist.id)}
                  >
                    Delete
                  </button>
                </div>
                {watchlist.items.length === 0 ? (
                  <div className="empty-state">No markets yet.</div>
                ) : (
                  <div className="stacked-cards compact-stack">
                    {watchlist.items.map((item) => (
                      <div key={item.id} className="list-row">
                        <div>
                          <strong>{item.market.title}</strong>
                          <small>
                            {item.market.category} · {Math.round(item.market.last_price * 100)}%
                          </small>
                        </div>
                        <button
                          type="button"
                          className="mini-button"
                          onClick={() => void handleRemoveWatchlistItem(watchlist.id, item.id)}
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </article>

        <article className="product-card">
          <span className="section-kicker">Saved Views</span>
          <h4>{savedViews.length} saved monitor states</h4>
          <div className="stacked-cards compact-stack">
            {savedViews.map((savedView) => (
              <div key={savedView.id} className="list-card">
                <div className="list-card-header">
                  <div>
                    <strong>{savedView.name}</strong>
                    <small>{getSavedViewDeskMode(savedView)} desk</small>
                  </div>
                  <div className="inline-actions">
                    <button
                      type="button"
                      className="mini-button"
                      onClick={() => handleOpenSavedView(savedView)}
                    >
                      Open
                    </button>
                    <button
                      type="button"
                      className="mini-button"
                      onClick={() => void handleDeleteSavedView(savedView.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <ul className="meta-list">
                  <li>Category: {String(savedView.filters_json?.categoryFilter ?? "all")}</li>
                  <li>Search: {String(savedView.filters_json?.searchQuery ?? "None")}</li>
                  <li>Pinned markets: {getSavedViewPinnedCount(savedView)}</li>
                </ul>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

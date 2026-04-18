import type { Market } from "../types/market";

const KEY_RECENT = "preterm:desk:recentMarkets";
const KEY_SMART = "preterm:desk:smartRanking";

export type RecentDeskOpen = { id: number; t: number };

export function recordMarketViewed(marketId: number): void {
  try {
    const raw = localStorage.getItem(KEY_RECENT);
    const list: RecentDeskOpen[] = raw ? JSON.parse(raw) : [];
    const next = [{ id: marketId, t: Date.now() }, ...list.filter((x) => x.id !== marketId)];
    localStorage.setItem(KEY_RECENT, JSON.stringify(next.slice(0, 50)));
  } catch {
    /* ignore quota / private mode */
  }
}

export function getSmartRankingPreference(): boolean {
  try {
    return localStorage.getItem(KEY_SMART) === "1";
  } catch {
    return false;
  }
}

export function setSmartRankingPreference(on: boolean): void {
  try {
    localStorage.setItem(KEY_SMART, on ? "1" : "0");
  } catch {
    /* ignore */
  }
}

function scoreMarket(
  marketId: number,
  recent: RecentDeskOpen[],
  watchlist: Set<number>,
  pinned: number[],
): number {
  let score = 0;
  const pinIndex = pinned.indexOf(marketId);
  if (pinIndex >= 0) {
    score += 42 - Math.min(pinIndex, 10) * 2;
  }
  if (watchlist.has(marketId)) {
    score += 72;
  }
  const recentIndex = recent.findIndex((x) => x.id === marketId);
  if (recentIndex >= 0) {
    const ageHours = (Date.now() - recent[recentIndex].t) / 3_600_000;
    score += Math.max(0, 48 - recentIndex * 4 - ageHours * 1.2);
  }
  return score;
}

/** Heuristic re-ordering from watchlists, pins, and recent opens (local activity signal). */
export function applySmartMonitorOrder(
  markets: Market[],
  watchlistMarketIds: Set<number>,
  pinnedMarketIds: number[],
): Market[] {
  let recent: RecentDeskOpen[] = [];
  try {
    const raw = localStorage.getItem(KEY_RECENT);
    recent = raw ? JSON.parse(raw) : [];
  } catch {
    recent = [];
  }
  return [...markets].sort((a, b) => {
    const sa = scoreMarket(a.id, recent, watchlistMarketIds, pinnedMarketIds);
    const sb = scoreMarket(b.id, recent, watchlistMarketIds, pinnedMarketIds);
    if (sb !== sa) {
      return sb - sa;
    }
    return a.title.localeCompare(b.title);
  });
}

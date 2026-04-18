import type { PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useMemo, useState } from "react";

type DeskMode = "overview" | "focused" | "event";

export type MonitorConfig = {
  deskMode: DeskMode;
  categoryFilter: string;
  searchQuery: string;
  selectedMarketId: number | null;
  pinnedMarketIds: number[];
};

type MonitorContextValue = {
  config: MonitorConfig;
  setDeskMode: (deskMode: DeskMode) => void;
  setCategoryFilter: (category: string) => void;
  setSearchQuery: (query: string) => void;
  setSelectedMarketId: (marketId: number | null) => void;
  togglePinnedMarket: (marketId: number) => void;
  applySavedView: (payload: Partial<MonitorConfig>) => void;
  createSavedViewPayload: () => {
    layout_json: Record<string, unknown>;
    filters_json: Record<string, unknown>;
  };
};

const MonitorContext = createContext<MonitorContextValue | undefined>(undefined);

const defaultConfig: MonitorConfig = {
  deskMode: "overview",
  categoryFilter: "all",
  searchQuery: "",
  selectedMarketId: null,
  pinnedMarketIds: [],
};

export function MonitorProvider({ children }: PropsWithChildren) {
  const [config, setConfig] = useState<MonitorConfig>(defaultConfig);
  const setDeskMode = useCallback(
    (deskMode: DeskMode) => setConfig((current) => ({ ...current, deskMode })),
    [],
  );
  const setCategoryFilter = useCallback(
    (categoryFilter: string) => setConfig((current) => ({ ...current, categoryFilter })),
    [],
  );
  const setSearchQuery = useCallback(
    (searchQuery: string) => setConfig((current) => ({ ...current, searchQuery })),
    [],
  );
  const setSelectedMarketId = useCallback(
    (selectedMarketId: number | null) =>
      setConfig((current) => ({ ...current, selectedMarketId })),
    [],
  );
  const togglePinnedMarket = useCallback(
    (marketId: number) =>
      setConfig((current) => ({
        ...current,
        pinnedMarketIds: current.pinnedMarketIds.includes(marketId)
          ? current.pinnedMarketIds.filter((id) => id !== marketId)
          : [...current.pinnedMarketIds, marketId],
      })),
    [],
  );
  const applySavedView = useCallback(
    (payload: Partial<MonitorConfig>) =>
      setConfig((current) => ({
        ...current,
        ...payload,
        pinnedMarketIds: Array.isArray(payload.pinnedMarketIds)
          ? payload.pinnedMarketIds.filter((id): id is number => typeof id === "number")
          : current.pinnedMarketIds,
      })),
    [],
  );
  const createSavedViewPayload = useCallback(
    () => ({
      layout_json: {
        selectedMarketId: config.selectedMarketId,
        pinnedMarketIds: config.pinnedMarketIds,
      },
      filters_json: {
        deskMode: config.deskMode,
        categoryFilter: config.categoryFilter,
        searchQuery: config.searchQuery,
      },
    }),
    [config],
  );

  const value = useMemo<MonitorContextValue>(
    () => ({
      config,
      setDeskMode,
      setCategoryFilter,
      setSearchQuery,
      setSelectedMarketId,
      togglePinnedMarket,
      applySavedView,
      createSavedViewPayload,
    }),
    [
      applySavedView,
      config,
      createSavedViewPayload,
      setCategoryFilter,
      setDeskMode,
      setSearchQuery,
      setSelectedMarketId,
      togglePinnedMarket,
    ],
  );

  return <MonitorContext.Provider value={value}>{children}</MonitorContext.Provider>;
}

export function useMonitor() {
  const context = useContext(MonitorContext);
  if (!context) {
    throw new Error("useMonitor must be used within a MonitorProvider.");
  }
  return context;
}

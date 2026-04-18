import type { PropsWithChildren } from "react";
import { createContext, useContext, useMemo, useState } from "react";

import type { HeadlineMapResult } from "../../api/headlines";

export type HeadlineMapSession = {
  headlineText: string;
  result: HeadlineMapResult;
};

type HeadlineMapContextValue = {
  recentHeadlineMap: HeadlineMapSession | null;
  setRecentHeadlineMap: (value: HeadlineMapSession | null) => void;
};

const HeadlineMapContext = createContext<HeadlineMapContextValue | undefined>(undefined);

export function HeadlineMapProvider({ children }: PropsWithChildren) {
  const [recentHeadlineMap, setRecentHeadlineMap] = useState<HeadlineMapSession | null>(null);
  const value = useMemo(
    () => ({
      recentHeadlineMap,
      setRecentHeadlineMap,
    }),
    [recentHeadlineMap],
  );

  return <HeadlineMapContext.Provider value={value}>{children}</HeadlineMapContext.Provider>;
}

export function useHeadlineMap() {
  const context = useContext(HeadlineMapContext);
  if (!context) {
    throw new Error("useHeadlineMap must be used within a HeadlineMapProvider.");
  }
  return context;
}

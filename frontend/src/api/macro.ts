import { apiRequest } from "./client";
import type { MacroContext } from "../types/macro";

export function getMarketMacroContext(marketId: number): Promise<MacroContext> {
  return apiRequest<MacroContext>(`/api/markets/${marketId}/macro-context`);
}

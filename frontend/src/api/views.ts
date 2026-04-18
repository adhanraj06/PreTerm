import { apiRequest } from "./client";
import type { SavedView } from "../types/watchlist";

type SavedViewPayload = {
  name: string;
  layout_json: Record<string, unknown>;
  filters_json: Record<string, unknown>;
};

export function getSavedViews(token: string): Promise<SavedView[]> {
  return apiRequest<SavedView[]>("/api/saved-views", { token });
}

export function createSavedView(
  token: string,
  payload: SavedViewPayload,
): Promise<SavedView> {
  return apiRequest<SavedView>("/api/saved-views", {
    method: "POST",
    token,
    body: payload,
  });
}

export function deleteSavedView(token: string, savedViewId: number): Promise<void> {
  return apiRequest<void>(`/api/saved-views/${savedViewId}`, {
    method: "DELETE",
    token,
  });
}

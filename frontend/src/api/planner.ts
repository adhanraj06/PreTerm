import { apiRequest } from "./client";
import type { PlannedEvent } from "../types/planner";

export function getPlannedEvents(token: string): Promise<PlannedEvent[]> {
  return apiRequest<PlannedEvent[]>("/api/planner/events", { token });
}

export function createPlannedEvent(
  token: string,
  payload: {
    title: string;
    date: string;
    location?: string;
    concern_type: string;
    notes?: string;
  },
): Promise<PlannedEvent> {
  return apiRequest<PlannedEvent>("/api/planner/events", {
    method: "POST",
    token,
    body: payload,
  });
}

export function deletePlannedEvent(token: string, plannedEventId: number): Promise<void> {
  return apiRequest<void>(`/api/planner/events/${plannedEventId}`, {
    method: "DELETE",
    token,
  });
}

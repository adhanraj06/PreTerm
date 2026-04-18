import { apiRequest } from "./client";

export type AlertPreference = {
  id: number;
  market_id: number | null;
  rule_type: string;
  threshold_value: number | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type Notification = {
  id: number;
  alert_preference_id: number | null;
  market_id: number | null;
  kind: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  metadata_json: Record<string, unknown> | null;
};

type AlertPreferencePayload = {
  market_id?: number | null;
  rule_type: string;
  threshold_value?: number | null;
  enabled: boolean;
};

export function getAlertPreferences(token: string): Promise<AlertPreference[]> {
  return apiRequest<AlertPreference[]>("/api/alerts/preferences", { token });
}

export function saveAlertPreference(
  token: string,
  payload: AlertPreferencePayload,
): Promise<AlertPreference> {
  return apiRequest<AlertPreference>("/api/alerts/preferences", {
    method: "POST",
    token,
    body: payload,
  });
}

export function getNotifications(token: string): Promise<Notification[]> {
  return apiRequest<Notification[]>("/api/alerts/notifications", { token });
}

export function markNotificationRead(
  token: string,
  notificationId: number,
): Promise<Notification> {
  return apiRequest<Notification>(`/api/alerts/notifications/${notificationId}/read`, {
    method: "POST",
    token,
  });
}

import { useEffect, useMemo, useState } from "react";

import {
  getAlertPreferences,
  saveAlertPreference,
  type AlertPreference,
} from "../../api/alerts";
import { getWatchlists } from "../../api/watchlists";
import type { Watchlist } from "../../types/watchlist";
import { useAuth } from "../auth/useAuth";

export function SettingsPage() {
  const { user, token } = useAuth();
  const [preferences, setPreferences] = useState<AlertPreference[]>([]);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    const authToken = token;

    let active = true;

    async function load() {
      try {
        const [prefs, watchlistData] = await Promise.all([
          getAlertPreferences(authToken),
          getWatchlists(authToken),
        ]);
        if (!active) {
          return;
        }
        setPreferences(prefs);
        setWatchlists(watchlistData);
      } catch (error) {
        if (!active) {
          return;
        }
        setStatusMessage(error instanceof Error ? error.message : "Unable to load alert settings.");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token]);

  const ruleMap = useMemo(
    () => Object.fromEntries(preferences.map((preference) => [preference.rule_type, preference])),
    [preferences],
  );

  async function upsertRule(ruleType: string, enabled: boolean, thresholdValue?: number | null) {
    if (!token) {
      return;
    }
    try {
      const saved = await saveAlertPreference(token, {
        rule_type: ruleType,
        enabled,
        threshold_value: thresholdValue ?? null,
      });
      setPreferences((current) => {
        const others = current.filter(
          (entry) => !(entry.rule_type === saved.rule_type && entry.market_id === saved.market_id),
        );
        return [saved, ...others];
      });
      setStatusMessage(`Updated ${ruleType.replace("_", " ")} alert.`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to update alert.");
    }
  }

  return (
    <div className="surface-stack">
      <section className="hero-panel compact">
        <div>
          <span className="section-kicker">Settings</span>
          <h3>Profile and preference controls</h3>
          <p>Use this route for user profile edits, desk defaults, and alert preferences.</p>
        </div>
      </section>

      {statusMessage ? <div className="flash-message">{statusMessage}</div> : null}

      <section className="two-up-grid">
        <article className="product-card">
          <span className="section-kicker">Account</span>
          <h4>{user?.display_name}</h4>
          <ul className="meta-list">
            <li>Email: {user?.email}</li>
            <li>Timezone: {user?.profile.timezone ?? "Not set"}</li>
            <li>Theme: {user?.profile.theme ?? "system"}</li>
          </ul>
        </article>

        <article className="product-card">
          <span className="section-kicker">Preferences</span>
          <h4>Desk Defaults</h4>
          <ul className="meta-list">
            <li>Categories: {user?.preference.preferred_categories.length}</li>
            <li>Desk mode: {user?.preference.preferred_desk_mode ?? "Unassigned"}</li>
            <li>
              Move threshold: {user?.preference.alert_move_threshold ?? "No threshold configured"}
            </li>
          </ul>
        </article>
      </section>

      <section className="two-up-grid">
        <article className="product-card">
          <span className="section-kicker">Alert Rules</span>
          <h4>Watchlist-aware triggers</h4>

          <div className="settings-rule-stack">
            <div className="settings-rule-row">
              <div>
                <strong>Market moved more than X%</strong>
                <small>Triggers when a watched market moves beyond your configured threshold.</small>
              </div>
              <div className="settings-rule-actions">
                <input
                  className="threshold-input"
                  type="number"
                  defaultValue={ruleMap.move_threshold?.threshold_value ?? 5}
                  onBlur={(event) =>
                    void upsertRule(
                      "move_threshold",
                      ruleMap.move_threshold?.enabled ?? true,
                      Number(event.target.value),
                    )
                  }
                />
                <button
                  type="button"
                  className={ruleMap.move_threshold?.enabled === false ? "ghost-button" : "primary-button"}
                  onClick={() =>
                    void upsertRule(
                      "move_threshold",
                      !(ruleMap.move_threshold?.enabled ?? true),
                      ruleMap.move_threshold?.threshold_value ?? 5,
                    )
                  }
                >
                  {ruleMap.move_threshold?.enabled === false ? "Enable" : "Enabled"}
                </button>
              </div>
            </div>

            <div className="settings-rule-row">
              <div>
                <strong>Watched market got a mapped headline</strong>
                <small>Triggers when headline-linked context exists for a watched market.</small>
              </div>
              <button
                type="button"
                className={ruleMap.mapped_headline?.enabled === false ? "ghost-button" : "primary-button"}
                onClick={() =>
                  void upsertRule("mapped_headline", !(ruleMap.mapped_headline?.enabled ?? true), null)
                }
              >
                {ruleMap.mapped_headline?.enabled === false ? "Enable" : "Enabled"}
              </button>
            </div>

            <div className="settings-rule-row">
              <div>
                <strong>Watched market entered a threshold range</strong>
                <small>Triggers when a watched market crosses a target probability level.</small>
              </div>
              <div className="settings-rule-actions">
                <input
                  className="threshold-input"
                  type="number"
                  defaultValue={ruleMap.threshold_range?.threshold_value ?? 60}
                  onBlur={(event) =>
                    void upsertRule(
                      "threshold_range",
                      ruleMap.threshold_range?.enabled ?? true,
                      Number(event.target.value),
                    )
                  }
                />
                <button
                  type="button"
                  className={ruleMap.threshold_range?.enabled === false ? "ghost-button" : "primary-button"}
                  onClick={() =>
                    void upsertRule(
                      "threshold_range",
                      !(ruleMap.threshold_range?.enabled ?? true),
                      ruleMap.threshold_range?.threshold_value ?? 60,
                    )
                  }
                >
                  {ruleMap.threshold_range?.enabled === false ? "Enable" : "Enabled"}
                </button>
              </div>
            </div>
          </div>
        </article>

        <article className="product-card">
          <span className="section-kicker">Why These Matter</span>
          <h4>Alerts connect directly to your saved workflow</h4>
          <ul className="meta-list">
            <li>Watchlists currently saved: {watchlists.length}</li>
            <li>Rules are most useful when important markets already live in watchlists.</li>
            <li>Notifications surface moves, mapped headlines, and range crossings as persistent items.</li>
            <li>This makes the desk feel active and personalized rather than stateless.</li>
          </ul>
        </article>
      </section>
    </div>
  );
}

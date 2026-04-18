import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createPlannedEvent, deletePlannedEvent, getPlannedEvents } from "../../api/planner";
import type { PlannedEvent } from "../../types/planner";
import { useAuth } from "../auth/useAuth";
import { useMonitor } from "../monitor/MonitorContext";

const concernOptions = [
  { value: "weather", label: "Outdoor event / weather risk" },
  { value: "travel", label: "Trip / travel cost risk" },
  { value: "game_day", label: "Game day / sports event" },
  { value: "policy", label: "Policy-sensitive date" },
  { value: "business", label: "Business-sensitive date" },
  { value: "crypto", label: "Crypto-sensitive date" },
];

const starterEvents = [
  {
    title: "Outdoor wedding weekend",
    date: "2026-06-20",
    location: "Austin, TX",
    concern_type: "weather",
    notes: "Concerned about weather, travel costs, and inflation-sensitive vendor expenses.",
  },
  {
    title: "Team offsite with investor update",
    date: "2026-09-15",
    location: "New York, NY",
    concern_type: "business",
    notes: "Need to monitor rates, equities sentiment, and any major company-specific moves.",
  },
];

export function PlannerPage() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { setSelectedMarketId } = useMonitor();
  const [events, setEvents] = useState<PlannedEvent[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    title: "",
    date: "",
    location: "",
    concern_type: "weather",
    notes: "",
  });

  useEffect(() => {
    if (!token) {
      return;
    }
    const authToken = token;

    let active = true;
    async function load() {
      try {
        const data = await getPlannedEvents(authToken);
        if (!active) {
          return;
        }
        setEvents(data);
      } catch {
        if (!active) {
          return;
        }
        setEvents([]);
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token]);

  async function handleCreate() {
    if (!token || !form.title.trim() || !form.date) {
      return;
    }

    setIsSaving(true);
    setStatusMessage(null);
    try {
      const created = await createPlannedEvent(token, {
        title: form.title,
        date: form.date,
        location: form.location || undefined,
        concern_type: form.concern_type,
        notes: form.notes || undefined,
      });
      setEvents((current) => [...current, created].sort((a, b) => a.date.localeCompare(b.date)));
      setForm({
        title: "",
        date: "",
        location: "",
        concern_type: "weather",
        notes: "",
      });
      setStatusMessage("Planned event added. Suggested monitoring markets are ready.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to create planned event.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(plannedEventId: number) {
    if (!token) {
      return;
    }
    try {
      await deletePlannedEvent(token, plannedEventId);
      setEvents((current) => current.filter((event) => event.id !== plannedEventId));
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Unable to delete planned event.");
    }
  }

  function openSuggestedMarket(marketId: number) {
    setSelectedMarketId(marketId);
    navigate(`/app/monitor/${marketId}`);
  }

  function applyStarter(index: number) {
    setForm(starterEvents[index]);
  }

  return (
    <div className="surface-stack">
      <section className="hero-panel compact">
        <div>
          <span className="section-kicker">Planner</span>
          <h3>Use markets as planning support, not just speculation.</h3>
          <p>
            Add a real-world event, describe the concern, and PreTerm suggests contracts worth
            monitoring as lightweight hedges or early-warning signals.
          </p>
        </div>
      </section>

      <section className="headline-map-layout">
        <article className="headline-input-card">
          <span className="section-kicker">New Planned Event</span>
          <h4>Personal hedge planner</h4>

          <div className="sample-chip-row">
            {starterEvents.map((event, index) => (
              <button
                key={event.title}
                type="button"
                className="sample-chip"
                onClick={() => applyStarter(index)}
              >
                {event.title}
              </button>
            ))}
          </div>

          <label className="field">
            <span>Event Title</span>
            <input
              type="text"
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              placeholder="Outdoor wedding, trip, launch date, game day"
            />
          </label>

          <div className="two-up-grid planner-grid-tight">
            <label className="field">
              <span>Date</span>
              <input
                type="date"
                value={form.date}
                onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))}
              />
            </label>

            <label className="field">
              <span>Location</span>
              <input
                type="text"
                value={form.location}
                onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))}
                placeholder="Chicago, IL"
              />
            </label>
          </div>

          <label className="field">
            <span>Concern Type</span>
            <select
              value={form.concern_type}
              onChange={(event) => setForm((current) => ({ ...current, concern_type: event.target.value }))}
            >
              {concernOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Notes</span>
            <textarea
              className="headline-textarea"
              value={form.notes}
              onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
              rows={5}
              placeholder="Explain the real-world risk you want to monitor through markets."
            />
          </label>

          {statusMessage ? <div className="flash-message">{statusMessage}</div> : null}

          <button
            type="button"
            className="primary-button"
            onClick={() => void handleCreate()}
            disabled={!form.title.trim() || !form.date || isSaving}
          >
            {isSaving ? "Saving Plan..." : "Create Planned Event"}
          </button>
        </article>

        <article className="headline-result-card">
          <span className="section-kicker">Your Plans</span>
          <h4>Suggested monitoring markets</h4>

          {events.length === 0 ? (
            <div className="empty-state">
              Create a planned event to see suggested contracts that can act as a decision-support layer.
            </div>
          ) : (
            <div className="headline-match-stack">
              {events.map((event) => (
                <div key={event.id} className="top-match-card">
                  <div className="top-match-header">
                    <div>
                      <span className="section-kicker">{event.concern_type}</span>
                      <h5>{event.title}</h5>
                    </div>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => void handleDelete(event.id)}
                    >
                      Remove
                    </button>
                  </div>

                  <div className="match-metrics">
                    <div>
                      <span className="section-kicker">Date</span>
                      <strong>{new Date(event.date).toLocaleDateString()}</strong>
                    </div>
                    <div>
                      <span className="section-kicker">Location</span>
                      <strong>{event.location ?? "Not set"}</strong>
                    </div>
                  </div>

                  {event.notes ? <p>{event.notes}</p> : null}

                  {event.suggestions.length === 0 ? (
                    <div className="empty-state">
                      No strong market suggestions yet. Try more specific notes or a different concern type.
                    </div>
                  ) : (
                    <div className="candidate-stack">
                      <span className="section-kicker">Suggested Markets</span>
                      {event.suggestions.map((suggestion) => (
                        <button
                          key={`${event.id}-${suggestion.market.id}`}
                          type="button"
                          className="candidate-card"
                          onClick={() => openSuggestedMarket(suggestion.market.id)}
                        >
                          <div>
                            <strong>{suggestion.market.title}</strong>
                            <small>
                              {suggestion.market.category} · {Math.round(suggestion.relevance_score * 100)}% fit
                            </small>
                            <small>{suggestion.rationale}</small>
                          </div>
                          <span className="impact-badge mixed">
                            {Math.round(suggestion.market.last_price * 100)}%
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </div>
  );
}

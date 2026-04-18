import { useMemo, useState } from "react";

import { MarketMoveChart } from "../charts/MarketMoveChart";
import type { MarketDetail } from "../../types/market";

type ScenarioMode = "bull" | "base" | "bear";
type BriefSection =
  | "drivers"
  | "bull_case"
  | "base_case"
  | "bear_case"
  | "catalysts"
  | "risks"
  | "what_would_change_probability";

const scenarioConfig: Record<
  ScenarioMode,
  { title: string; label: string; tone: string; narrative: (market: MarketDetail) => string }
> = {
  bull: {
    title: "Upside Framing",
    label: "Bull",
    tone: "scenario-bull",
    narrative: (market) => market.brief?.bull_case ?? "",
  },
  base: {
    title: "Base Case",
    label: "Base",
    tone: "scenario-base",
    narrative: (market) => market.brief?.base_case ?? "",
  },
  bear: {
    title: "Downside Framing",
    label: "Bear",
    tone: "scenario-bear",
    narrative: (market) => market.brief?.bear_case ?? "",
  },
};

const sectionLabels: Record<BriefSection, string> = {
  drivers: "Drivers",
  bull_case: "Bull Case",
  base_case: "Base Case",
  bear_case: "Bear Case",
  catalysts: "Catalysts",
  risks: "Risks",
  what_would_change_probability: "What Would Change This Probability",
};

function formatTimelineStamp(iso: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
}

export function EventBriefPanel({
  market,
  showStandaloneChart = false,
}: {
  market: MarketDetail;
  /** When true, the parent renders the price chart; this panel skips the duplicate chart card. */
  showStandaloneChart?: boolean;
}) {
  const [scenarioMode, setScenarioMode] = useState<ScenarioMode>("base");
  const [activeSection, setActiveSection] = useState<BriefSection>("drivers");

  const brief = market.brief;

  const sectionContent = useMemo(() => {
    if (!brief) {
      return "";
    }
    return brief[activeSection];
  }, [activeSection, brief]);

  if (!brief) {
    return (
      <section className="event-brief-panel event-brief-panel--compact">
        <p className="detail-description">
          There isn&apos;t a generated brief for this contract in the database yet. It will appear after the next Kalshi
          refresh cycle.
        </p>
      </section>
    );
  }

  return (
    <section className="event-brief-panel">
      <div className="event-brief-header">
        <div>
          <span className="section-kicker">Event Brief</span>
          <h3>{market.title}</h3>
          <p>{brief.summary}</p>
        </div>
        <div className="brief-scorecard">
          <span className="section-kicker">Now</span>
          <strong>{Math.round(market.last_price * 100)}%</strong>
          <small>
            {market.probability_change >= 0 ? "+" : ""}
            {Math.round(market.probability_change * 100)} pts recent move
          </small>
        </div>
      </div>

      <div className="brief-context-grid">
        <article className="brief-context-card">
          <span className="section-kicker">Why This Matters Now</span>
          <p>{brief.why_this_matters_now}</p>
        </article>
        <article className="brief-context-card">
          <span className="section-kicker">What Changed</span>
          <p>{brief.what_changed}</p>
        </article>
      </div>

      <div className="scenario-toggle-strip">
        {(["bull", "base", "bear"] as ScenarioMode[]).map((mode) => (
          <button
            key={mode}
            type="button"
            className={scenarioMode === mode ? `scenario-toggle active ${scenarioConfig[mode].tone}` : "scenario-toggle"}
            onClick={() => {
              setScenarioMode(mode);
              setActiveSection(`${mode}_case` as BriefSection);
            }}
          >
            <span>{scenarioConfig[mode].label}</span>
          </button>
        ))}
      </div>

      <div className={`scenario-frame ${scenarioConfig[scenarioMode].tone}`}>
        <span className="section-kicker">{scenarioConfig[scenarioMode].title}</span>
        <p>{scenarioConfig[scenarioMode].narrative(market)}</p>
      </div>

      <div className="brief-workbench">
        <div className="brief-nav">
          {(Object.keys(sectionLabels) as BriefSection[]).map((section) => (
            <button
              key={section}
              type="button"
              className={activeSection === section ? "brief-nav-button active" : "brief-nav-button"}
              onClick={() => setActiveSection(section)}
            >
              {sectionLabels[section]}
            </button>
          ))}
        </div>

        <div className="brief-body-card">
          <span className="section-kicker">{sectionLabels[activeSection]}</span>
          <p>{sectionContent}</p>
        </div>
      </div>

      {showStandaloneChart ? (
        <div className="brief-foot-grid brief-foot-grid--single">
          <article className="brief-foot-card">
            <span className="section-kicker">Move Timeline</span>
            {market.timeline_entries.length === 0 ? (
              <div className="empty-state">No move timeline is available yet.</div>
            ) : (
              <div className="timeline-stack">
                {market.timeline_entries
                  .slice()
                  .reverse()
                  .map((entry) => (
                    <div key={entry.id} className="timeline-row">
                      <div className="timeline-stamp">
                        <strong>{formatTimelineStamp(entry.occurred_at)}</strong>
                      </div>
                      <div className="timeline-content">
                        <div className="timeline-move">
                          <span className={entry.move && entry.move >= 0 ? "delta positive" : "delta negative"}>
                            {entry.move && entry.move >= 0 ? "+" : ""}
                            {entry.move ? Math.round(entry.move * 100) : 0} pts
                          </span>
                          {entry.linked_label ? (
                            <small>
                              {entry.linked_type ?? "context"}: {entry.linked_label}
                            </small>
                          ) : null}
                        </div>
                        <p>{entry.reason}</p>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </article>
        </div>
      ) : (
        <div className="brief-foot-grid">
          <article className="brief-foot-card">
            <span className="section-kicker">Historical Context</span>
            <MarketMoveChart market={market} />
          </article>

          <article className="brief-foot-card">
            <span className="section-kicker">Move Timeline</span>
            {market.timeline_entries.length === 0 ? (
              <div className="empty-state">No move timeline is available yet.</div>
            ) : (
              <div className="timeline-stack">
                {market.timeline_entries
                  .slice()
                  .reverse()
                  .map((entry) => (
                    <div key={entry.id} className="timeline-row">
                      <div className="timeline-stamp">
                        <strong>{formatTimelineStamp(entry.occurred_at)}</strong>
                      </div>
                      <div className="timeline-content">
                        <div className="timeline-move">
                          <span className={entry.move && entry.move >= 0 ? "delta positive" : "delta negative"}>
                            {entry.move && entry.move >= 0 ? "+" : ""}
                            {entry.move ? Math.round(entry.move * 100) : 0} pts
                          </span>
                          {entry.linked_label ? (
                            <small>
                              {entry.linked_type ?? "context"}: {entry.linked_label}
                            </small>
                          ) : null}
                        </div>
                        <p>{entry.reason}</p>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </article>
        </div>
      )}

      <div className="brief-foot-grid">
        <article className="brief-foot-card">
          <span className="section-kicker">Recent Headlines</span>
          {brief.recent_headlines_json.length === 0 ? (
            <div className="empty-state">
              No curated headlines are attached to this ticker yet. Use the Headlines desk to map wire copy to markets.
            </div>
          ) : (
            <div className="headline-stack">
              {brief.recent_headlines_json.map((headline) => (
                <div key={`${headline.source}-${headline.published_at}-${headline.title}`} className="headline-card">
                  <strong>{headline.title}</strong>
                  <small>
                    {headline.source} · {new Date(headline.published_at).toLocaleString()}
                  </small>
                  <p>{headline.why_it_matters}</p>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="brief-foot-card">
          <span className="section-kicker">Reference Inputs</span>
          <div className="source-chip-row">
            {brief.sources_json.map((source) => (
              <span key={`${source.type}-${source.label}`} className="source-chip">
                {source.type}: {source.label}
              </span>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}

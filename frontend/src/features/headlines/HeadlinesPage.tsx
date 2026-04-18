import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { mapHeadline, type HeadlineMapResult } from "../../api/headlines";
import { fetchRedditNews, fetchRssNews, type NewsItem } from "../../api/news";
import {
  analyzeSentimentRedditHot,
  analyzeSentimentText,
  analyzeSentimentUrl,
  type SentimentResult,
} from "../../api/sentiment";
import { useMonitor } from "../monitor/MonitorContext";
import { useHeadlineMap } from "./HeadlineMapContext";

const sampleHeadlines = [
  "Cooler CPI print boosts odds of multiple Fed cuts this year",
  "Spot bitcoin ETF inflows surge as BTC pushes toward fresh highs",
  "Generic ballot shifts toward Democrats as suburban polling tightens",
  "Hyperscaler capex commentary keeps Nvidia revenue expectations elevated",
];

const sampleSentimentTexts = [
  "Bitcoin ETF inflows accelerated again and traders are leaning toward a breakout if macro liquidity stays supportive.",
  "Multiple hot inflation components raise the risk that the Fed stays restrictive longer than the market expects.",
  "Polling remains mixed, but the latest district-level movement looks slightly better for Democrats than last month.",
];

type HeadlinesMode = "mapping" | "sentiment";

export function HeadlinesPage() {
  const navigate = useNavigate();
  const { setSelectedMarketId } = useMonitor();
  const { setRecentHeadlineMap } = useHeadlineMap();
  const [mode, setMode] = useState<HeadlinesMode>("mapping");

  const [headlineText, setHeadlineText] = useState(sampleHeadlines[0]);
  const [result, setResult] = useState<HeadlineMapResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sentimentText, setSentimentText] = useState(sampleSentimentTexts[0]);
  const [sentimentUrl, setSentimentUrl] = useState("");
  const [sentimentResult, setSentimentResult] = useState<SentimentResult | null>(null);
  const [isRunningSentiment, setIsRunningSentiment] = useState(false);
  const [sentimentError, setSentimentError] = useState<string | null>(null);

  const [redditSubreddit, setRedditSubreddit] = useState("worldnews");
  const [wireHeadlines, setWireHeadlines] = useState<NewsItem[]>([]);
  const [wireBusy, setWireBusy] = useState(false);
  const [wireError, setWireError] = useState<string | null>(null);

  async function pullRedditHeadlines() {
    setWireError(null);
    setWireBusy(true);
    try {
      const res = await fetchRedditNews(redditSubreddit.trim().replace(/^r\//i, ""), 12);
      setWireHeadlines(res.items);
    } catch (err) {
      setWireError(err instanceof Error ? err.message : "Could not load Reddit.");
    } finally {
      setWireBusy(false);
    }
  }

  async function pullBbcHeadlines() {
    setWireError(null);
    setWireBusy(true);
    try {
      const res = await fetchRssNews("bbc_world", 14);
      setWireHeadlines(res.items);
    } catch (err) {
      setWireError(err instanceof Error ? err.message : "Could not load RSS.");
    } finally {
      setWireBusy(false);
    }
  }

  async function runMapping(text: string) {
    setError(null);
    setIsRunning(true);
    try {
      const response = await mapHeadline(text);
      setResult(response);
      setRecentHeadlineMap({ headlineText: text, result: response });
    } catch (mappingError) {
      setError(mappingError instanceof Error ? mappingError.message : "Headline mapping failed.");
    } finally {
      setIsRunning(false);
    }
  }

  async function runSentimentText(text: string) {
    setSentimentError(null);
    setIsRunningSentiment(true);
    try {
      const response = await analyzeSentimentText({ text });
      setSentimentResult(response);
    } catch (analysisError) {
      setSentimentError(
        analysisError instanceof Error ? analysisError.message : "Sentiment analysis failed.",
      );
    } finally {
      setIsRunningSentiment(false);
    }
  }

  async function runSentimentUrl() {
    setSentimentError(null);
    setIsRunningSentiment(true);
    try {
      const response = await analyzeSentimentUrl(sentimentUrl);
      setSentimentResult(response);
    } catch (analysisError) {
      setSentimentError(
        analysisError instanceof Error ? analysisError.message : "URL sentiment analysis failed.",
      );
    } finally {
      setIsRunningSentiment(false);
    }
  }

  async function runRedditHotSentiment() {
    setSentimentError(null);
    setIsRunningSentiment(true);
    try {
      const response = await analyzeSentimentRedditHot({
        subreddit: redditSubreddit.trim().replace(/^r\//i, ""),
        limit: 10,
      });
      setSentimentResult(response);
    } catch (analysisError) {
      setSentimentError(
        analysisError instanceof Error ? analysisError.message : "Reddit sentiment failed.",
      );
    } finally {
      setIsRunningSentiment(false);
    }
  }

  function jumpToMarket(marketId: number) {
    setSelectedMarketId(marketId);
    navigate(`/app/monitor/${marketId}`);
  }

  return (
    <div className="surface-stack">
      <section className="hero-panel compact">
        <div>
          <span className="section-kicker">Headlines Desk</span>
          <h3>Map events to markets and score narrative tone with market context.</h3>
          <p>
            Map headlines to Kalshi contracts, pull live Reddit or BBC World RSS without API keys, and run VADER
            sentiment on pasted text, article URLs, or an entire subreddit&apos;s hot feed in one shot.
          </p>
        </div>
      </section>

      <section className="scenario-toggle-strip">
        <button
          type="button"
          className={mode === "mapping" ? "scenario-toggle active scenario-base" : "scenario-toggle"}
          onClick={() => setMode("mapping")}
        >
          <span>Headline Map</span>
        </button>
        <button
          type="button"
          className={mode === "sentiment" ? "scenario-toggle active scenario-bull" : "scenario-toggle"}
          onClick={() => setMode("sentiment")}
        >
          <span>Sentiment</span>
        </button>
      </section>

      {mode === "mapping" ? (
        <section className="headline-map-layout">
          <article className="headline-input-card">
            <span className="section-kicker">Input</span>
            <h4>Headline to market</h4>

            <label className="field">
              <span>Headline Text</span>
              <textarea
                className="headline-textarea"
                value={headlineText}
                onChange={(event) => setHeadlineText(event.target.value)}
                placeholder="Paste a headline or event summary"
                rows={5}
              />
            </label>

            <div className="sample-chip-row">
              {sampleHeadlines.map((sample) => (
                <button
                  key={sample}
                  type="button"
                  className="sample-chip"
                  onClick={() => {
                    setHeadlineText(sample);
                    void runMapping(sample);
                  }}
                >
                  {sample}
                </button>
              ))}
            </div>

            <div className="live-wire-block">
              <span className="section-kicker">Live wire</span>
              <div className="live-wire-actions">
                <label className="field">
                  <span>Subreddit</span>
                  <input
                    value={redditSubreddit}
                    onChange={(event) => setRedditSubreddit(event.target.value)}
                    placeholder="worldnews"
                  />
                </label>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => void pullRedditHeadlines()}
                  disabled={wireBusy || redditSubreddit.trim().length < 2}
                >
                  {wireBusy ? "Loading…" : "Reddit hot"}
                </button>
                <button type="button" className="ghost-button" onClick={() => void pullBbcHeadlines()} disabled={wireBusy}>
                  BBC World RSS
                </button>
              </div>
              {wireError ? <div className="form-error">{wireError}</div> : null}
              {wireHeadlines.length > 0 ? (
                <ul className="live-wire-list">
                  {wireHeadlines.map((item) => (
                    <li key={`${item.source ?? "src"}-${item.title}`}>
                      <button
                        type="button"
                        onClick={() => {
                          setHeadlineText(item.title);
                          void runMapping(item.title);
                        }}
                      >
                        <strong>{item.title}</strong>
                        {item.source ? (
                          <small>
                            {" "}
                            · {item.source}
                          </small>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>

            {error ? <div className="form-error">{error}</div> : null}

            <button
              type="button"
              className="primary-button"
              onClick={() => void runMapping(headlineText)}
              disabled={headlineText.trim().length < 8 || isRunning}
            >
              {isRunning ? "Mapping Headline..." : "Run Headline Map"}
            </button>
          </article>

          <article className="headline-result-card">
            <span className="section-kicker">Result</span>
            <h4>Mapped market</h4>

            {!result?.top_match ? (
              <div className="empty-state">
                Run a headline to see the top market match, directional impact, and deterministic explanation.
              </div>
            ) : (
              <div className="headline-match-stack">
                <div className="top-match-card">
                  <div className="top-match-header">
                    <div>
                      <span className="section-kicker">Top Match</span>
                      <h5>{result.top_match.title}</h5>
                    </div>
                    <span className={`impact-badge ${result.top_match.directional_impact}`}>
                      {result.top_match.directional_impact}
                    </span>
                  </div>

                  <div className="match-metrics">
                    <div>
                      <span className="section-kicker">Category</span>
                      <strong>{result.top_match.category}</strong>
                    </div>
                    <div>
                      <span className="section-kicker">Match Strength</span>
                      <strong>{Math.round(result.top_match.match_strength * 100)}%</strong>
                    </div>
                  </div>

                  <p>{result.top_match.explanation}</p>
                  <div className="headline-why-card">
                    <span className="section-kicker">Why It Matters</span>
                    <p>{result.top_match.why_it_matters}</p>
                  </div>

                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => jumpToMarket(result.top_match!.market_id)}
                  >
                    Open Matched Market Brief
                  </button>
                </div>

                {result.candidates.length > 1 ? (
                  <div className="candidate-stack">
                    <span className="section-kicker">Other Candidates</span>
                    {result.candidates.slice(1).map((candidate) => (
                      <button
                        key={`${candidate.market_id}-${candidate.title}`}
                        type="button"
                        className="candidate-card"
                        onClick={() => jumpToMarket(candidate.market_id)}
                      >
                        <div>
                          <strong>{candidate.title}</strong>
                          <small>
                            {candidate.category} · {Math.round(candidate.match_strength * 100)}% match
                          </small>
                        </div>
                        <span className={`impact-badge ${candidate.directional_impact}`}>
                          {candidate.directional_impact}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            )}
          </article>
        </section>
      ) : (
        <section className="headline-map-layout">
          <article className="headline-input-card">
            <span className="section-kicker">Sentiment Input</span>
            <h4>Text or URL to market tone</h4>

            <label className="field">
              <span>Pasted Text</span>
              <textarea
                className="headline-textarea"
                value={sentimentText}
                onChange={(event) => setSentimentText(event.target.value)}
                placeholder="Paste a headline, Reddit post text, or news excerpt"
                rows={6}
              />
            </label>

            <div className="sample-chip-row">
              {sampleSentimentTexts.map((sample) => (
                <button
                  key={sample}
                  type="button"
                  className="sample-chip"
                  onClick={() => {
                    setSentimentText(sample);
                    void runSentimentText(sample);
                  }}
                >
                  {sample}
                </button>
              ))}
            </div>

            <label className="field">
              <span>Public URL</span>
              <input
                type="url"
                value={sentimentUrl}
                onChange={(event) => setSentimentUrl(event.target.value)}
                placeholder="https://… (optional if you use Reddit hot below)"
              />
            </label>

            <div className="live-wire-block">
              <span className="section-kicker">Reddit without a thread URL</span>
              <p className="inline-note">
                Fetches public JSON for the subreddit&apos;s hot page, blends titles/selftext, and scores the bundle.
              </p>
              <label className="field">
                <span>Subreddit</span>
                <input
                  value={redditSubreddit}
                  onChange={(event) => setRedditSubreddit(event.target.value)}
                  placeholder="worldnews"
                />
              </label>
              <button
                type="button"
                className="primary-button"
                onClick={() => void runRedditHotSentiment()}
                disabled={redditSubreddit.trim().length < 2 || isRunningSentiment}
              >
                {isRunningSentiment ? "Analyzing…" : "Analyze subreddit hot"}
              </button>
            </div>

            {sentimentError ? <div className="form-error">{sentimentError}</div> : null}

            <div className="inline-actions">
              <button
                type="button"
                className="primary-button"
                onClick={() => void runSentimentText(sentimentText)}
                disabled={sentimentText.trim().length < 8 || isRunningSentiment}
              >
                {isRunningSentiment ? "Analyzing..." : "Analyze Text"}
              </button>
              <button
                type="button"
                className="ghost-button"
                onClick={() => void runSentimentUrl()}
                disabled={sentimentUrl.trim().length < 10 || isRunningSentiment}
              >
                Analyze URL
              </button>
            </div>
          </article>

          <article className="headline-result-card">
            <span className="section-kicker">Sentiment Output</span>
            <h4>Market-relevant tone</h4>

            {!sentimentResult ? (
              <div className="empty-state">
                Run sentiment analysis to see the VADER score, directional label, and matched market if the text is relevant.
              </div>
            ) : (
              <div className="headline-match-stack">
                <div className="top-match-card">
                  <div className="top-match-header">
                    <div>
                      <span className="section-kicker">Analyzed Source</span>
                      <h5>{sentimentResult.title_text}</h5>
                    </div>
                    <span className={`impact-badge ${sentimentResult.sentiment_label}`}>
                      {sentimentResult.sentiment_label}
                    </span>
                  </div>

                  <div className="match-metrics">
                    <div>
                      <span className="section-kicker">Source</span>
                      <strong>{sentimentResult.source_label?.trim() || sentimentResult.source}</strong>
                    </div>
                    <div>
                      <span className="section-kicker">Compound Score</span>
                      <strong>{sentimentResult.compound_score.toFixed(3)}</strong>
                    </div>
                  </div>

                  {sentimentResult.extraction_note ? (
                    <div className="headline-why-card">
                      <span className="section-kicker">Extraction Note</span>
                      <p>{sentimentResult.extraction_note}</p>
                    </div>
                  ) : null}

                  {sentimentResult.matched_market ? (
                    <div className="headline-why-card">
                      <span className="section-kicker">Related Market</span>
                      <p>{sentimentResult.matched_market.title}</p>
                      <p>{sentimentResult.matched_market.why_it_matters}</p>
                      <button
                        type="button"
                        className="primary-button"
                        onClick={() => jumpToMarket(sentimentResult.matched_market!.market_id)}
                      >
                        Open Related Market Brief
                      </button>
                    </div>
                  ) : (
                    <div className="empty-state">
                      No strong market match was found. Try more market-specific text or use the headline map tab.
                    </div>
                  )}
                </div>
              </div>
            )}
          </article>
        </section>
      )}
    </div>
  );
}

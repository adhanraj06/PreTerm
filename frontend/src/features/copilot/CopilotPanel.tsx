import { useEffect, useMemo, useState } from "react";

import {
  buildCopilotMarketContext,
  buildCopilotWatchlistContext,
  chatWithCopilot,
  type CopilotChatResponse,
} from "../../api/copilot";
import { getMarket, getMarkets } from "../../api/markets";
import { getWatchlists } from "../../api/watchlists";
import type { Market, MarketDetail } from "../../types/market";
import type { Watchlist } from "../../types/watchlist";
import { useAuth } from "../auth/useAuth";
import { useHeadlineMap } from "../headlines/HeadlineMapContext";
import { useMonitor } from "../monitor/MonitorContext";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: CopilotChatResponse["source"];
};

const starterPrompts = [
  "Explain the selected market in plain market terms.",
  "Summarize the bull, base, and bear cases.",
  "What would need to happen for this market to move materially?",
  "Compare this contract with the most related pinned market.",
];

export function CopilotPanel() {
  const { token } = useAuth();
  const { config } = useMonitor();
  const { recentHeadlineMap } = useHeadlineMap();
  const [allMarkets, setAllMarkets] = useState<Market[]>([]);
  const [selectedMarket, setSelectedMarket] = useState<MarketDetail | null>(null);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "PreTerm Copilot is ready. I’ll use the selected market, pinned contracts, watchlists, and recent headline-map context when available.",
      source: "mock",
    },
  ]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadBase() {
      try {
        const [marketList, watchlistData] = await Promise.all([
          getMarkets(),
          token ? getWatchlists(token) : Promise.resolve([]),
        ]);
        if (!active) {
          return;
        }
        setAllMarkets(marketList);
        setWatchlists(watchlistData);
      } catch {
        if (!active) {
          return;
        }
        setAllMarkets([]);
        setWatchlists([]);
      }
    }
    void loadBase();
    return () => {
      active = false;
    };
  }, [token]);

  useEffect(() => {
    if (!config.selectedMarketId) {
      setSelectedMarket(null);
      return;
    }
    let active = true;
    async function loadSelected() {
      try {
        const detail = await getMarket(config.selectedMarketId as number);
        if (!active) {
          return;
        }
        setSelectedMarket(detail);
      } catch {
        if (!active) {
          return;
        }
        setSelectedMarket(null);
      }
    }
    void loadSelected();
    return () => {
      active = false;
    };
  }, [config.selectedMarketId]);

  const pinnedMarkets = useMemo(
    () => allMarkets.filter((market) => config.pinnedMarketIds.includes(market.id)),
    [allMarkets, config.pinnedMarketIds],
  );

  async function handleSend(rawMessage?: string) {
    const message = (rawMessage ?? draft).trim();
    if (!message || !token) {
      return;
    }

    setError(null);
    setDraft("");
    setMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: message,
      },
    ]);
    setIsSending(true);

    try {
      const selectedContext = buildCopilotMarketContext(selectedMarket);
      const pinnedContexts = pinnedMarkets.map((market) => {
        if (selectedMarket && selectedMarket.id === market.id) {
          return buildCopilotMarketContext(selectedMarket);
        }

        return {
          id: market.id,
          title: market.title,
          category: market.category,
          status: market.status,
          last_price: market.last_price,
          probability_change: market.probability_change,
          description: market.description,
          summary: null,
          why_this_matters_now: null,
          what_changed: null,
          bull_case: null,
          base_case: null,
          bear_case: null,
          catalysts: null,
          drivers: null,
          risks: null,
          what_would_change_probability: null,
        };
      }).filter((market): market is NonNullable<typeof market> => market !== null);

      const response = await chatWithCopilot(token, {
        message,
        selected_market: selectedContext,
        pinned_markets: pinnedContexts,
        watchlists: buildCopilotWatchlistContext(watchlists),
        recent_headline_map: recentHeadlineMap
          ? {
              headline_text: recentHeadlineMap.headlineText,
              top_match: recentHeadlineMap.result.top_match,
              candidates: recentHeadlineMap.result.candidates,
            }
          : null,
      });

      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.response_text,
          source: response.source,
        },
      ]);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Copilot request failed.");
    } finally {
      setIsSending(false);
    }
  }

  const contextSummary = useMemo(() => {
    const lines: string[] = [];
    if (selectedMarket) {
      lines.push(`Selected: ${selectedMarket.title}`);
    }
    if (config.pinnedMarketIds.length > 0) {
      lines.push(`Pinned: ${config.pinnedMarketIds.length}`);
    }
    if (watchlists.length > 0) {
      lines.push(`Watchlists: ${watchlists.length}`);
    }
    if (recentHeadlineMap?.result.top_match) {
      lines.push(`Headline map: ${recentHeadlineMap.result.top_match.title}`);
    }
    return lines;
  }, [config.pinnedMarketIds.length, recentHeadlineMap, selectedMarket, watchlists.length]);

  return (
    <div className="copilot-panel">
      <div className="insight-card copilot-card">
        <div className="panel-heading">
          <div>
            <span className="section-kicker">Market Copilot</span>
            <h3>Context-aware interpretation</h3>
          </div>
          <small>{selectedMarket ? "Market-linked" : "Awaiting context"}</small>
        </div>

        <div className="context-chip-row">
          {contextSummary.length === 0 ? (
            <span className="context-chip muted">No active workstation context</span>
          ) : (
            contextSummary.map((item) => (
              <span key={item} className="context-chip">
                {item}
              </span>
            ))
          )}
        </div>

        <div className="starter-prompt-grid">
          {starterPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="sample-chip"
              onClick={() => void handleSend(prompt)}
              disabled={isSending}
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="copilot-thread">
          {messages.map((message) => (
            <div
              key={message.id}
              className={message.role === "assistant" ? "chat-bubble assistant" : "chat-bubble user"}
            >
              <div className="chat-bubble-meta">
                <strong>{message.role === "assistant" ? "Copilot" : "You"}</strong>
                {message.source ? <small>{message.source}</small> : null}
              </div>
              <p>{message.content}</p>
            </div>
          ))}
          {isSending ? <div className="chat-bubble assistant loading">Analyzing current market context...</div> : null}
        </div>

        {error ? <div className="form-error">{error}</div> : null}

        <div className="copilot-composer">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask about the selected market, a mapped headline, or what would need to happen next."
            rows={4}
          />
          <button
            type="button"
            className="primary-button"
            disabled={draft.trim().length < 2 || isSending || !token}
            onClick={() => void handleSend()}
          >
            {isSending ? "Thinking..." : "Send to Copilot"}
          </button>
        </div>
      </div>
    </div>
  );
}

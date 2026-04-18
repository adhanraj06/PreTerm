from typing import Iterable

from app.core.config import settings
from app.integrations.gemini_client import GeminiClient
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotMarketContext,
    CopilotReference,
)


SYSTEM_PROMPT = """
You are PreTerm Copilot, a prediction-market interpretation assistant embedded inside a market workstation.

Your job:
- Explain the selected market in market-specific terms.
- Compare related contracts when the user asks.
- Summarize bull, base, and bear cases succinctly.
- Answer conditional questions like "what would need to happen for X?"
- Explain how a headline or catalyst could affect the market's implied probability.

Operating rules:
- Be concise, analytical, and specific to the provided market context.
- Treat prices as implied probabilities, not certainties.
- Distinguish what changed, what matters now, and what would change your view.
- If the context is incomplete, say what is missing instead of inventing facts.
- Do not provide trading, legal, or financial advice.
- Do not act like a generic chatbot. Stay inside the workstation context.
- Prefer short paragraphs and compact bullets only when they improve clarity.
""".strip()


def _render_market_context(market: CopilotMarketContext) -> str:
    return (
        f"Market: {market.title}\n"
        f"Category: {market.category}\n"
        f"Status: {market.status}\n"
        f"Current probability: {round(market.last_price * 100)}%\n"
        f"Recent move: {round(market.probability_change * 100, 1)} pts\n"
        f"Description: {market.description or 'N/A'}\n"
        f"Summary: {market.summary or 'N/A'}\n"
        f"Why now: {market.why_this_matters_now or 'N/A'}\n"
        f"What changed: {market.what_changed or 'N/A'}\n"
        f"Bull case: {market.bull_case or 'N/A'}\n"
        f"Base case: {market.base_case or 'N/A'}\n"
        f"Bear case: {market.bear_case or 'N/A'}\n"
        f"Drivers: {market.drivers or 'N/A'}\n"
        f"Catalysts: {market.catalysts or 'N/A'}\n"
        f"Risks: {market.risks or 'N/A'}\n"
        f"What changes probability: {market.what_would_change_probability or 'N/A'}"
    )


def _render_markets(title: str, markets: Iterable[CopilotMarketContext]) -> str:
    values = list(markets)
    if not values:
        return f"{title}: none"
    lines = [title + ":"]
    for market in values:
        lines.append(
            f"- {market.title} ({market.category}, {round(market.last_price * 100)}%, "
            f"move {round(market.probability_change * 100, 1)} pts)"
        )
    return "\n".join(lines)


def build_user_prompt(payload: CopilotChatRequest) -> str:
    sections = [f"User question:\n{payload.message.strip()}"]

    if payload.selected_market:
        sections.append("Selected market context:\n" + _render_market_context(payload.selected_market))

    sections.append(_render_markets("Pinned markets", payload.pinned_markets))

    if payload.watchlists:
        watchlist_lines = ["Watchlists:"]
        for watchlist in payload.watchlists:
            item_titles = ", ".join(market.title for market in watchlist.markets[:6]) or "No markets"
            watchlist_lines.append(f"- {watchlist.name}: {item_titles}")
        sections.append("\n".join(watchlist_lines))

    if payload.recent_headline_map:
        top_match = payload.recent_headline_map.top_match
        sections.append(
            "Recent headline mapping:\n"
            f"Headline: {payload.recent_headline_map.headline_text}\n"
            f"Top match: {top_match.title if top_match else 'None'}\n"
            f"Impact: {top_match.directional_impact if top_match else 'unknown'}\n"
            f"Why it matters: {top_match.why_it_matters if top_match else 'N/A'}"
        )

    sections.append(
        "Response format:\n"
        "1. Lead with the direct answer.\n"
        "2. Reference the selected market or related markets explicitly.\n"
        "3. If useful, close with a short 'What would change this view' sentence."
    )
    return "\n\n".join(sections)


def _build_references(payload: CopilotChatRequest) -> list[CopilotReference]:
    references: list[CopilotReference] = []
    if payload.selected_market:
        references.append(CopilotReference(label=payload.selected_market.title, type="selected_market"))
    for market in payload.pinned_markets[:3]:
        references.append(CopilotReference(label=market.title, type="pinned_market"))
    if payload.recent_headline_map and payload.recent_headline_map.top_match:
        references.append(
            CopilotReference(
                label=payload.recent_headline_map.headline_text[:80],
                type="headline_map",
            )
        )
    return references


def build_mock_response(payload: CopilotChatRequest) -> str:
    selected = payload.selected_market
    if selected is None:
        return (
            "I need an active market selection to give a grounded interpretation. "
            "Pick a market or run a headline map, and I can explain the implied probability, "
            "the main drivers, and what would need to change for the contract to reprice."
        )

    prompt = payload.message.lower()
    if "headline" in prompt and payload.recent_headline_map:
        top_match = payload.recent_headline_map.top_match
        return (
            f"The headline matters because it changes the path for {selected.title}. "
            f"Right now the market is pricing about {round(selected.last_price * 100)}%, so the question is "
            f"whether the event is incremental to the base case or strong enough to shift the path. "
            f"{top_match.why_it_matters if top_match else selected.why_this_matters_now or ''}".strip()
        )
    if "compare" in prompt and payload.pinned_markets:
        peer = payload.pinned_markets[0]
        return (
            f"{selected.title} is the primary contract to watch because it carries the clearest direct signal. "
            f"Compared with {peer.title}, it is more immediately tied to the catalyst path in the brief. "
            f"The current framing is: bull case, {selected.bull_case or 'upside follow-through'}; "
            f"base case, {selected.base_case or 'partial confirmation'}; "
            f"bear case, {selected.bear_case or 'mean reversion if incoming data disappoints'}."
        )
    if "what would need to happen" in prompt or "need to happen" in prompt:
        return (
            f"For {selected.title} to move materially from the current {round(selected.last_price * 100)}%, "
            f"the market would need new evidence on the core drivers: {selected.drivers or 'policy, data, and positioning'}. "
            f"The clearest repricing trigger would be {selected.what_would_change_probability or selected.catalysts or 'a catalyst that changes the base case'}."
        )
    return (
        f"{selected.title} is currently pricing about {round(selected.last_price * 100)}%. "
        f"The main issue is {selected.why_this_matters_now or selected.summary or 'whether the current path keeps holding'}. "
        f"What changed recently: {selected.what_changed or 'the market has repriced around incoming catalysts'}. "
        f"Base case: {selected.base_case or 'the current path mostly holds'}. "
        f"What would change this view: {selected.what_would_change_probability or selected.risks or 'new information that weakens the current driver set'}."
    )


async def chat_with_copilot(payload: CopilotChatRequest) -> CopilotChatResponse:
    references = _build_references(payload)
    if not settings.gemini_api_key:
        return CopilotChatResponse(
            response_text=build_mock_response(payload),
            source="mock",
            references=references,
        )

    user_prompt = build_user_prompt(payload)
    client = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    try:
        text = await client.generate_text(SYSTEM_PROMPT, user_prompt)
        return CopilotChatResponse(response_text=text, source="gemini", references=references)
    except Exception:
        return CopilotChatResponse(
            response_text=build_mock_response(payload),
            source="mock",
            references=references,
        )

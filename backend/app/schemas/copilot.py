from pydantic import BaseModel, ConfigDict, Field


class CopilotMarketContext(BaseModel):
    id: int
    title: str
    category: str
    status: str
    last_price: float
    probability_change: float
    description: str | None = None
    summary: str | None = None
    why_this_matters_now: str | None = None
    what_changed: str | None = None
    bull_case: str | None = None
    base_case: str | None = None
    bear_case: str | None = None
    catalysts: str | None = None
    drivers: str | None = None
    risks: str | None = None
    what_would_change_probability: str | None = None


class CopilotWatchlistContext(BaseModel):
    id: int
    name: str
    markets: list[CopilotMarketContext] = Field(default_factory=list)


class CopilotHeadlineMapCandidate(BaseModel):
    market_id: int
    title: str
    category: str
    match_strength: float
    directional_impact: str
    explanation: str
    why_it_matters: str


class CopilotHeadlineMapContext(BaseModel):
    headline_text: str
    top_match: CopilotHeadlineMapCandidate | None = None
    candidates: list[CopilotHeadlineMapCandidate] = Field(default_factory=list)


class CopilotChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    selected_market: CopilotMarketContext | None = None
    pinned_markets: list[CopilotMarketContext] = Field(default_factory=list)
    watchlists: list[CopilotWatchlistContext] = Field(default_factory=list)
    recent_headline_map: CopilotHeadlineMapContext | None = None


class CopilotReference(BaseModel):
    label: str
    type: str


class CopilotChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_text: str
    source: str
    references: list[CopilotReference] = Field(default_factory=list)

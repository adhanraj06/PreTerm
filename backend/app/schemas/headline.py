from pydantic import BaseModel, Field


class HeadlineMapRequest(BaseModel):
    headline_text: str = Field(min_length=8, max_length=500)


class HeadlineMapCandidate(BaseModel):
    market_id: int
    title: str
    category: str
    match_strength: float
    directional_impact: str
    explanation: str
    why_it_matters: str


class HeadlineMapResponse(BaseModel):
    top_match: HeadlineMapCandidate | None
    candidates: list[HeadlineMapCandidate]

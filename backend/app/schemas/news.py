from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    title: str
    text: str
    url: str | None = None
    source: str | None = None
    score: int | None = None


class NewsFeedResponse(BaseModel):
    items: list[NewsItem] = Field(default_factory=list)

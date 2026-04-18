from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="seed")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_price: Mapped[float] = mapped_column(Float, nullable=False)
    probability_change: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_interest: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshots: Mapped[list["MarketSnapshot"]] = relationship(
        back_populates="market",
        cascade="all, delete-orphan",
        order_by="MarketSnapshot.captured_at",
    )
    timeline_entries: Mapped[list["MarketTimelineEntry"]] = relationship(
        back_populates="market",
        cascade="all, delete-orphan",
        order_by="MarketTimelineEntry.occurred_at",
    )
    brief: Mapped["MarketBrief | None"] = relationship(
        back_populates="market",
        cascade="all, delete-orphan",
        uselist=False,
    )
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(back_populates="market")
    alert_preferences: Mapped[list["AlertPreference"]] = relationship(back_populates="market")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="market")


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_interest: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    market: Mapped["Market"] = relationship(back_populates="snapshots")


class MarketBrief(Base):
    __tablename__ = "market_briefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_id: Mapped[int] = mapped_column(
        ForeignKey("markets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    why_this_matters_now: Mapped[str] = mapped_column(Text, nullable=False)
    what_changed: Mapped[str] = mapped_column(Text, nullable=False)
    bull_case: Mapped[str] = mapped_column(Text, nullable=False)
    base_case: Mapped[str] = mapped_column(Text, nullable=False)
    bear_case: Mapped[str] = mapped_column(Text, nullable=False)
    catalysts: Mapped[str] = mapped_column(Text, nullable=False)
    drivers: Mapped[str] = mapped_column(Text, nullable=False)
    risks: Mapped[str] = mapped_column(Text, nullable=False)
    what_would_change_probability: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recent_headlines_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    market: Mapped["Market"] = relationship(back_populates="brief")


class MarketTimelineEntry(Base):
    __tablename__ = "market_timeline_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    move: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_after_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    linked_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    linked_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    market: Mapped["Market"] = relationship(back_populates="timeline_entries")

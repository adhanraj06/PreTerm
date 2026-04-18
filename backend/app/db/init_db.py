from app.models.alert import AlertPreference, Notification
from app.db.base import Base
from app.db.session import engine
from app.models.market import Market, MarketBrief, MarketSnapshot, MarketTimelineEntry
from app.models.planner import PlannedEvent
from app.models.saved_view import SavedView
from app.models.user import User, UserPreference, UserProfile
from app.models.watchlist import Watchlist, WatchlistItem


def initialize_database() -> None:
    """Create all tables required for the current application scope."""
    Base.metadata.create_all(bind=engine)

from fastapi import APIRouter

from app.api.routes import alerts, auth, copilot, finance, headlines, health, markets, news, planner, research, sentiment, views, watchlists


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
api_router.include_router(markets.router, prefix="/markets", tags=["markets"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(planner.router, prefix="/planner", tags=["planner"])
api_router.include_router(headlines.router, prefix="", tags=["headlines"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(views.router, prefix="/saved-views", tags=["saved-views"])

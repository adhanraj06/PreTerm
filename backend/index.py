"""Vercel FastAPI Web Service entrypoint (service root = `backend/`)."""

from app.main import app

__all__ = ["app"]

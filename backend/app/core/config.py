import os
from functools import lru_cache
from typing import Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    # Vercel serverless: deployment dir is not writable; /tmp is.
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return "sqlite:////tmp/preterm.db"
    return "sqlite:///./preterm.db"


class Settings(BaseSettings):
    app_name: str = "PreTerm API"
    app_env: str = "development"
    api_v1_prefix: str = "/api"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = True
    app_workers: int = 1
    log_level: str = "info"
    database_url: str = Field(default_factory=_default_database_url)
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_demo_user: bool = True
    demo_user_email: str = "demo@preterm.local"
    demo_user_password: str = "demo12345"
    demo_user_display_name: str = "PreTerm Demo"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    fred_api_key: str | None = None
    market_data_provider: str = "kalshi"
    market_data_refresh_seconds: int = 300
    kalshi_api_base: str = "https://api.elections.kalshi.com/trade-api/v2"
    kalshi_market_limit: int = 20
    kalshi_market_status: str = "open"
    kalshi_series_filter: list[str] = []
    kalshi_fallback_to_seeded: bool = True
    kalshi_request_timeout_seconds: float = 10.0
    kalshi_candlestick_delay_seconds: float = 0.22
    kalshi_max_429_retries: int = 6
    #: When True, every market refresh hits the candlesticks endpoint (heavy; easy429s). Default off: use last/previous price snapshots.
    kalshi_fetch_candlesticks_on_refresh: bool = False
    kalshi_brief_use_gemini: bool = False
    fred_api_base: str = "https://api.stlouisfed.org/fred"
    fred_csv_path: str | None = None
    enable_yfinance: bool = True
    enable_edgar: bool = True
    edgar_identity: str | None = None
    sec_data_api_base: str = "https://data.sec.gov"
    sec_user_agent: str = "PreTerm/0.1 support@example.com"
    serve_frontend: bool = False
    frontend_dist_dir: str = "../frontend/dist"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )

    @model_validator(mode="after")
    def normalize_postgres_url(self) -> Self:
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            self.database_url = "postgresql+psycopg2://" + url.removeprefix("postgres://")
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            self.database_url = "postgresql+psycopg2://" + url.removeprefix("postgresql://")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("kalshi_series_filter", mode="before")
    @classmethod
    def parse_series_filter(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

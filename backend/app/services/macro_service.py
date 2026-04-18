from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.integrations.fred_client import FredClient
from app.models.market import Market
from app.schemas.macro import MacroContextResponse, MacroObservationRead, MacroSeriesRead
from app.services.market_service import get_market_by_id


@dataclass(frozen=True)
class SeriesDefinition:
    series_id: str
    title: str
    units: str
    frequency: str = "Monthly"
    csv_series_id: str | None = None
    csv_title: str | None = None
    csv_units: str | None = None
    csv_frequency: str | None = None


SERIES_LIBRARY: dict[str, SeriesDefinition] = {
    "cpi": SeriesDefinition("CPIAUCSL", "Consumer Price Index (All Urban)", "Index 1982-84=100"),
    "core_cpi": SeriesDefinition(
        "CPILFESL",
        "Core CPI (Less Food & Energy)",
        "Index 1982-84=100",
        csv_series_id="CPIULFSL",
        csv_title="Core CPI (all items less food, SA)",
        csv_units="Index 1982-84=100",
    ),
    "pce": SeriesDefinition("PCEPI", "PCE Price Index", "Index 2017=100", frequency="Monthly"),
    "core_pce": SeriesDefinition("PCEPILFE", "Core PCE Price Index", "Index 2017=100", frequency="Monthly"),
    "unemployment": SeriesDefinition("UNRATE", "Unemployment Rate", "Percent"),
    "payrolls": SeriesDefinition("PAYEMS", "Total Nonfarm Payrolls", "Thousands of Persons"),
    "participation": SeriesDefinition("CIVPART", "Labor Force Participation Rate", "Percent"),
    "claims": SeriesDefinition(
        "ICSA",
        "Initial Jobless Claims",
        "Number",
        frequency="Weekly",
        csv_series_id="CLAIMSx",
        csv_title="Initial jobless claims (monthly column in bundle)",
        csv_frequency="Monthly",
    ),
    "fed_funds": SeriesDefinition("FEDFUNDS", "Effective Federal Funds Rate (Monthly Avg)", "Percent"),
    "fed_funds_daily": SeriesDefinition("DFF", "Effective Federal Funds Rate (Daily)", "Percent", frequency="Daily"),
    "gs1m": SeriesDefinition(
        "DGS1MO",
        "1-Month Treasury Constant Maturity",
        "Percent",
        frequency="Daily",
        csv_series_id="TB3MS",
        csv_title="3-Month Treasury Bill (closest short rate in bundle)",
        csv_frequency="Monthly",
    ),
    "gs3m": SeriesDefinition(
        "DGS3MO",
        "3-Month Treasury Constant Maturity",
        "Percent",
        frequency="Daily",
        csv_series_id="TB6MS",
        csv_title="6-Month Treasury Bill",
        csv_frequency="Monthly",
    ),
    "gs2": SeriesDefinition("DGS2", "2-Year Treasury Constant Maturity", "Percent", frequency="Daily"),
    "gs5": SeriesDefinition(
        "DGS5",
        "5-Year Treasury Constant Maturity",
        "Percent",
        frequency="Daily",
        csv_series_id="GS5",
        csv_frequency="Monthly",
    ),
    "gs10": SeriesDefinition(
        "DGS10",
        "10-Year Treasury Constant Maturity",
        "Percent",
        frequency="Daily",
        csv_series_id="GS10",
        csv_frequency="Monthly",
    ),
    "gs30": SeriesDefinition("DGS30", "30-Year Treasury Constant Maturity", "Percent", frequency="Daily"),
    "t10y2y": SeriesDefinition("T10Y2Y", "10-Year minus 2-Year Treasury Spread", "Percent", frequency="Daily"),
    "mortgage30": SeriesDefinition("MORTGAGE30US", "30-Year Fixed Rate Mortgage Average", "Percent", frequency="Weekly"),
    "m2": SeriesDefinition("M2SL", "M2 Money Stock", "Billions of Dollars"),
    "gdp_real": SeriesDefinition("GDPC1", "Real GDP", "Billions of Chained 2017 Dollars", frequency="Quarterly"),
    "gdp_nominal": SeriesDefinition("GDP", "Nominal GDP", "Billions of Dollars", frequency="Quarterly"),
    "indpro": SeriesDefinition("INDPRO", "Industrial Production Index", "Index 2017=100"),
    "retail": SeriesDefinition(
        "RSXFS",
        "Retail Sales Ex Food Services",
        "Millions of Dollars",
        csv_series_id="RETAILx",
        csv_title="Retail sales (bundle series)",
    ),
    "housing_starts": SeriesDefinition("HOUST", "Housing Starts", "Thousands of Units"),
    "sentiment": SeriesDefinition(
        "UMCSENT",
        "U. of Michigan Consumer Sentiment",
        "Index 1966:Q1=100",
        csv_series_id="UMCSENTx",
    ),
    "dollar_broad": SeriesDefinition(
        "DTWEXBGS",
        "Trade Weighted U.S. Dollar Index (Broad)",
        "Index Jan 2006=100",
        frequency="Daily",
        csv_series_id="TWEXAFEGSMTHx",
        csv_title="Trade-weighted dollar index (monthly bundle)",
        csv_frequency="Monthly",
    ),
    "wti": SeriesDefinition(
        "DCOILWTICO",
        "Crude Oil WTI Spot",
        "Dollars per Barrel",
        frequency="Daily",
        csv_series_id="OILPRICEx",
        csv_title="Oil price (producer index, monthly bundle)",
        csv_frequency="Monthly",
    ),
    "vix": SeriesDefinition(
        "VIXCLS",
        "CBOE Volatility Index: VIX",
        "Index",
        frequency="Daily",
        csv_series_id="VIXCLSx",
        csv_frequency="Monthly",
    ),
    "hy_spread": SeriesDefinition("BAMLH0A0HYM2", "ICE BofA US High Yield OAS", "Percent", frequency="Daily"),
    "recession": SeriesDefinition(
        "USREC",
        "NBER Recession Indicator",
        "Binary",
        csv_series_id="INDPRO",
        csv_title="Industrial Production Index (activity proxy in CSV bundle)",
        csv_units="Index 2017=100",
    ),
}


def _market_metadata_tags(market: Market) -> set[str]:
    if not market.metadata_json:
        return set()
    try:
        metadata = json.loads(market.metadata_json)
    except json.JSONDecodeError:
        return set()
    tags = metadata.get("tags", [])
    if isinstance(tags, list):
        return {str(tag).lower() for tag in tags}
    return set()


def _relevant_series_keys(market: Market) -> list[str]:
    tags = _market_metadata_tags(market)
    title = (market.title or "").lower()
    description = (market.description or "").lower()
    text = f"{title} {description}"

    if market.category != "macro" and not (
        {"fed", "cpi", "inflation", "recession", "labor", "unemployment", "treasury", "yields"}
        & tags
    ):
        return []

    keys: list[str] = []
    if "fed" in tags or "rates" in tags or "funds" in text or "rate cut" in text:
        keys.extend(["fed_funds", "cpi", "unemployment"])
    if "cpi" in tags or "inflation" in tags or "disinflation" in tags:
        keys.extend(["cpi", "fed_funds", "unemployment"])
    if "recession" in tags or "growth" in tags or "recession" in text:
        keys.extend(["recession", "unemployment", "fed_funds"])
    if "treasury" in tags or "yields" in tags or "10-year" in text or "10 year" in text:
        keys.extend(["gs10", "fed_funds", "cpi"])

    if not keys and market.category == "macro":
        keys = ["fed_funds", "cpi", "unemployment"]

    seen: set[str] = set()
    ordered: list[str] = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered[:4]


def _parse_observations(raw_observations: list[dict[str, object]]) -> list[MacroObservationRead]:
    observations: list[MacroObservationRead] = []
    for raw in raw_observations:
        raw_date = raw.get("date")
        raw_value = raw.get("value")
        if not isinstance(raw_date, str) or raw_value in (None, "."):
            continue
        try:
            parsed_date = datetime.fromisoformat(raw_date).date()
            parsed_value = float(str(raw_value))
        except ValueError:
            continue
        observations.append(MacroObservationRead(date=parsed_date, value=parsed_value))
    return observations


def _load_series(
    client: FredClient,
    definition: SeriesDefinition,
    *,
    observation_limit: int | None = None,
) -> MacroSeriesRead | None:
    observation_start = (datetime.now(UTC) - timedelta(days=365 * 5)).date()
    limit = observation_limit if observation_limit is not None else 48

    if client.uses_fred_api():
        metadata = client.get_series(definition.series_id)
        if metadata is None:
            return None
        raw_observations = client.get_series_observations(
            definition.series_id,
            observation_start=observation_start,
            limit=limit,
        )
        title = str(metadata.get("title") or definition.title)
        units = str(metadata.get("units_short") or metadata.get("units") or definition.units)
        frequency = str(metadata.get("frequency_short") or metadata.get("frequency") or definition.frequency)
    else:
        if not client.csv_available():
            return None
        column = definition.csv_series_id or definition.series_id
        raw_observations = client.get_csv_observations(
            column,
            observation_start=observation_start,
            limit=limit,
        )
        title = definition.csv_title or definition.title
        units = definition.csv_units or definition.units
        frequency = definition.csv_frequency or definition.frequency

    observations = _parse_observations(raw_observations)
    if not observations:
        return None

    latest = observations[-1].value if observations else None
    previous = observations[-2].value if len(observations) > 1 else None
    change = latest - previous if latest is not None and previous is not None else None
    display_id = definition.csv_series_id if not client.uses_fred_api() and definition.csv_series_id else definition.series_id

    return MacroSeriesRead(
        series_id=display_id,
        title=title,
        units=units,
        frequency=frequency,
        latest_value=latest,
        previous_value=previous,
        change=change,
        observations=observations,
    )


def get_macro_context(db: Session, market_id: int) -> MacroContextResponse | None:
    market = get_market_by_id(db, market_id)
    if market is None:
        return None

    orm_market = db.get(Market, market_id)
    if orm_market is None:
        return None

    series_keys = _relevant_series_keys(orm_market)
    if not series_keys:
        return MacroContextResponse(
            available=False,
            reason="No macro context is configured for this market.",
            market_id=market.id,
            market_title=market.title,
            series=[],
            macro_source=None,
        )

    client = FredClient()
    if not client.uses_fred_api() and not client.csv_available():
        return MacroContextResponse(
            available=False,
            reason="Macro data unavailable: add FRED_API_KEY or place fred.csv next to the backend / repo root.",
            market_id=market.id,
            market_title=market.title,
            series=[],
            macro_source=None,
        )

    macro_source = "fred_api" if client.uses_fred_api() else "fred_csv"
    series_payload: list[MacroSeriesRead] = []
    try:
        for key in series_keys:
            loaded = _load_series(client, SERIES_LIBRARY[key])
            if loaded is not None:
                series_payload.append(loaded)
    except Exception:
        return MacroContextResponse(
            available=False,
            reason="Macro data request failed. The workstation is falling back without macro context.",
            market_id=market.id,
            market_title=market.title,
            series=[],
            macro_source=macro_source,
        )

    if not series_payload:
        return MacroContextResponse(
            available=False,
            reason="No usable macro series were returned for this market.",
            market_id=market.id,
            market_title=market.title,
            series=[],
            macro_source=macro_source,
        )

    return MacroContextResponse(
        available=True,
        market_id=market.id,
        market_title=market.title,
        series=series_payload,
        macro_source=macro_source,
    )


def list_research_macro_catalog() -> list[dict[str, str]]:
    client = FredClient()
    rows = [{"key": key, "title": definition.title} for key, definition in SERIES_LIBRARY.items()]
    if client.uses_fred_api():
        return sorted(rows, key=lambda r: (r["title"].lower(), r["key"]))
    if not client.csv_available():
        return []
    headers = set(client.get_csv_headers())
    filtered: list[dict[str, str]] = []
    for key, definition in SERIES_LIBRARY.items():
        column = definition.csv_series_id or definition.series_id
        if column in headers:
            filtered.append({"key": key, "title": definition.title})
    return sorted(filtered, key=lambda r: (r["title"].lower(), r["key"]))


def get_research_macro_series(series_key: str) -> MacroSeriesRead | None:
    definition = SERIES_LIBRARY.get(series_key)
    if definition is None:
        return None
    client = FredClient()
    if not client.uses_fred_api() and not client.csv_available():
        return None
    return _load_series(client, definition, observation_limit=120)

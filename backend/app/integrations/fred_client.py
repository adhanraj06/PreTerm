from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from threading import Lock

import httpx

from app.core.config import settings


class FredClient:
    _csv_lock = Lock()
    _csv_headers: list[str] | None = None
    _csv_rows: list[list[str]] | None = None
    _csv_loaded_path: str | None = None

    def __init__(self) -> None:
        self.base_url = settings.fred_api_base.rstrip("/")

    @staticmethod
    def _integration_dir() -> Path:
        return Path(__file__).resolve().parent

    @staticmethod
    def _candidate_bases() -> tuple[Path, ...]:
        here = FredClient._integration_dir()
        backend_root = here.parents[2]
        repo_root = here.parents[3]
        return (Path.cwd(), backend_root, repo_root)

    def _resolve_csv_path(self) -> Path | None:
        if settings.fred_csv_path:
            raw = Path(settings.fred_csv_path)
            candidates = [raw] if raw.is_absolute() else [base / raw for base in self._candidate_bases()]
            for cand in candidates:
                resolved = cand.resolve()
                if resolved.is_file():
                    return resolved
            return None

        for base in self._candidate_bases():
            cand = (base / "fred.csv").resolve()
            if cand.is_file():
                return cand
        return None

    def _load_csv_disk(self, path: Path) -> tuple[list[str], list[list[str]]]:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            headers = next(reader, [])
            rows: list[list[str]] = []
            for row in reader:
                if not row or not row[0]:
                    continue
                if row[0].startswith("Transform"):
                    continue
                try:
                    datetime.strptime(row[0].strip(), "%m/%d/%Y")
                except ValueError:
                    continue
                if len(row) < len(headers):
                    row = row + [""] * (len(headers) - len(row))
                rows.append(row[: len(headers)])
        return headers, rows

    def _ensure_csv(self) -> None:
        path = self._resolve_csv_path()
        key = str(path) if path else ""
        with self._csv_lock:
            if self._csv_rows is not None and self._csv_loaded_path == key:
                return
            if path is None:
                self._csv_headers = []
                self._csv_rows = []
                self._csv_loaded_path = key
                return
            self._csv_headers, self._csv_rows = self._load_csv_disk(path)
            self._csv_loaded_path = key

    def csv_available(self) -> bool:
        self._ensure_csv()
        return bool(self._csv_rows and self._csv_headers)

    def get_csv_headers(self) -> list[str]:
        self._ensure_csv()
        return list(self._csv_headers or [])

    def uses_fred_api(self) -> bool:
        return bool(settings.fred_api_key)

    def _get(self, path: str, params: dict[str, object]) -> dict[str, object]:
        with httpx.Client(base_url=self.base_url, timeout=10.0) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    def get_series(self, series_id: str) -> dict[str, object] | None:
        if not self.uses_fred_api():
            return None
        payload = self._get(
            "/series",
            {
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "series_id": series_id,
            },
        )
        series = payload.get("seriess", [])
        return series[0] if series else None

    def get_series_observations(
        self,
        series_id: str,
        observation_start: date,
        limit: int = 24,
    ) -> list[dict[str, object]]:
        if not self.uses_fred_api():
            return []
        payload = self._get(
            "/series/observations",
            {
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "series_id": series_id,
                "observation_start": observation_start.isoformat(),
                "sort_order": "asc",
                "limit": limit,
            },
        )
        return payload.get("observations", [])

    def get_csv_observations(
        self,
        column_name: str,
        observation_start: date,
        limit: int = 40,
    ) -> list[dict[str, object]]:
        """Read observations from bundled fred.csv (wide monthly table)."""
        self._ensure_csv()
        headers = self._csv_headers or []
        rows = self._csv_rows or []
        if not headers or not rows:
            return []

        try:
            col_idx = headers.index(column_name)
        except ValueError:
            return []

        parsed: list[tuple[date, float]] = []
        for row in rows:
            try:
                row_date = datetime.strptime(row[0].strip(), "%m/%d/%Y").date()
            except ValueError:
                continue
            if row_date < observation_start:
                continue
            raw_val = row[col_idx].strip() if col_idx < len(row) else ""
            if raw_val in ("", "."):
                continue
            try:
                parsed.append((row_date, float(raw_val)))
            except ValueError:
                continue

        parsed.sort(key=lambda item: item[0])
        tail = parsed[-limit:] if limit > 0 else parsed
        return [{"date": d.isoformat(), "value": str(v)} for d, v in tail]

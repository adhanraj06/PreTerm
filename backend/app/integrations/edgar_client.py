from __future__ import annotations

import functools
from datetime import date

import httpx

from app.core.config import settings

# Legacy hand-mapped CIKs for httpx fallback when edgartools is unavailable.
CIK_LOOKUP: dict[str, tuple[str, str]] = {
    "NVDA": ("0001045810", "NVIDIA CORP"),
    "TSLA": ("0001318605", "TESLA INC"),
    "AMZN": ("0001018724", "AMAZON COM INC"),
}


@functools.lru_cache(maxsize=1)
def _sec_company_tickers_map() -> dict[str, tuple[str, str]] | None:
    """Map upper ticker -> (CIK 10-digit, company name) from SEC company_tickers.json."""
    identity = (settings.edgar_identity or settings.sec_user_agent or "PreTerm Research (university) contact@example.com").strip()
    headers = {
        "User-Agent": identity,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    try:
        with httpx.Client(headers=headers, timeout=25.0, follow_redirects=True) as client:
            response = client.get("https://www.sec.gov/files/company_tickers.json")
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    out: dict[str, tuple[str, str]] = {}
    for row in payload.values():
        if not isinstance(row, dict):
            continue
        sym = str(row.get("ticker") or "").strip().upper()
        if not sym:
            continue
        try:
            cik_int = int(row["cik_str"])
        except (KeyError, TypeError, ValueError):
            continue
        name = str(row.get("title") or sym)
        out[sym] = (str(cik_int).zfill(10), name)
    return out


def _lookup_ticker_cik(ticker: str) -> tuple[str, str] | None:
    upper = ticker.strip().upper()
    if upper in CIK_LOOKUP:
        raw, name = CIK_LOOKUP[upper]
        return raw.zfill(10), name
    cmap = _sec_company_tickers_map()
    if cmap is None:
        return None
    return cmap.get(upper)


class EdgarClient:
    def _identity(self) -> str:
        return (settings.edgar_identity or settings.sec_user_agent or "PreTerm User support@example.com").strip()

    def fetch_filings(
        self,
        ticker: str,
        *,
        forms: list[str] | None = None,
        limit: int = 12,
    ) -> dict[str, object] | None:
        """List recent SEC filings using edgartools (preferred) or SEC submissions JSON."""
        if not settings.enable_edgar:
            return None

        forms = [f.strip().upper() for f in (forms or ["10-K", "10-Q", "8-K"]) if f.strip()]
        if not forms:
            forms = ["10-K", "10-Q", "8-K"]
        limit = max(1, min(limit, 40))

        via_library = self._fetch_via_edgartools(ticker, forms, limit)
        if via_library is not None:
            return via_library

        return self._fetch_via_submissions(ticker, forms, limit)

    def _fetch_via_edgartools(
        self,
        ticker: str,
        forms: list[str],
        limit: int,
    ) -> dict[str, object] | None:
        try:
            from edgar import Company, set_identity
        except ImportError:
            return None

        try:
            set_identity(self._identity())
            company = Company(ticker.strip().upper())
        except Exception:
            return None

        per_form = max(1, limit // len(forms))
        filings: list[dict[str, object]] = []
        try:
            for form in forms:
                try:
                    batch = company.get_filings(form=form).head(per_form + 1)
                except Exception:
                    continue
                for filing in batch:
                    if len(filings) >= limit:
                        break
                    try:
                        filing_date = date.fromisoformat(str(filing.filing_date))
                    except ValueError:
                        continue
                    filings.append(
                        {
                            "form": str(filing.form),
                            "filing_date": filing_date,
                            "description": f"SEC {filing.form} via EDGAR.",
                            "document_url": str(filing.url) if filing.url else None,
                        }
                    )
                if len(filings) >= limit:
                    break
        except Exception:
            return None

        filings.sort(key=lambda row: row["filing_date"], reverse=True)
        filings = filings[:limit]

        cik_val = getattr(company, "cik", None)
        cik_str = str(int(cik_val)) if cik_val is not None else ""

        return {
            "company_name": str(company.name or ticker.upper()),
            "cik": cik_str,
            "latest_filings": filings,
        }

    def _fetch_via_submissions(
        self,
        ticker: str,
        forms: list[str],
        limit: int,
    ) -> dict[str, object] | None:
        resolved = _lookup_ticker_cik(ticker)
        if resolved is None:
            return None

        cik, company_name = resolved
        headers = {
            "User-Agent": (settings.edgar_identity or settings.sec_user_agent or "PreTerm Research contact@example.com").strip(),
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        }
        url = f"{settings.sec_data_api_base}/submissions/CIK{cik}.json"

        try:
            with httpx.Client(headers=headers, timeout=10.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return None

        form_filter = {f.upper() for f in forms}
        recent = payload.get("filings", {}).get("recent", {})
        raw_forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        filings: list[dict[str, object]] = []
        for form, filing_date, accession, primary_doc in zip(
            raw_forms,
            dates,
            accessions,
            primary_docs,
            strict=False,
        ):
            if str(form).upper() not in form_filter:
                continue
            accession_compact = str(accession).replace("-", "")
            document_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik, 10)}/{accession_compact}/{primary_doc}"
                if primary_doc
                else None
            )
            filings.append(
                {
                    "form": str(form),
                    "filing_date": date.fromisoformat(str(filing_date)),
                    "description": f"Recent {form} filing from SEC EDGAR.",
                    "document_url": document_url,
                }
            )
            if len(filings) >= limit:
                break

        return {
            "company_name": str(payload.get("name") or company_name),
            "cik": cik,
            "latest_filings": filings,
        }

    def get_company_context(self, ticker: str) -> dict[str, object] | None:
        return self.fetch_filings(ticker, forms=["10-K", "10-Q", "8-K"], limit=9)

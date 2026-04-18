# PreTerm

**PreTerm** is a prediction-market workstation: one place to watch **Kalshi-style binary contracts** (with seeded fallback), read **event briefs** and probability history, **map headlines** to the right market, run **sentiment** on text or feeds, **research** equities, SEC filings, and **FRED** macro series, save **watchlists** and **desk layouts**, plan real-world dates with **suggested contracts**, tune **alerts**, and chat with a **context-aware Copilot**.

This repository is the full-stack application (FastAPI + React). Implied prices are **market consensus**, not guarantees about outcomes.

**Repository:** [github.com/adhanraj06/PreTerm](https://github.com/adhanraj06/PreTerm)

---

## Features

| Area | What you get |
|------|----------------|
| **Monitor** | Contract grid with filters, pins, smart sort, closing-date view; full detail with chart, brief, timeline. |
| **Event brief** | Summary, why now, what changed, drivers, catalysts, risks, bull/base/bear, scenario workbench. |
| **Headlines** | Headline → ranked markets; VADER sentiment on text, URLs, or Reddit hot; BBC/RSS live wire. |
| **Research** | Yahoo quote + news bundle, SEC EDGAR filings, FRED macro catalog (API or bundled `fred.csv`). |
| **Watchlists & saved views** | Named lists and snapshots of desk mode, search, category, pins. |
| **Planner** | Dated real-world events with concern type → suggested monitoring contracts. |
| **Settings** | Profile snapshot, alert rules (move threshold, headline mapping, probability range). |
| **Copilot** | Right-rail assistant using selected market, pins, watchlists, last headline map; Gemini when configured, mock fallback otherwise. |

---

## Stack

- **Backend:** Python 3, **FastAPI**, SQLAlchemy, SQLite (default), httpx, optional yfinance / edgartools / NLTK (VADER).
- **Frontend:** **React 18**, **TypeScript**, **Vite**, **React Router**, **Recharts**.
- **Integrations (optional):** Kalshi Trade API, FRED API or local CSV, Yahoo Finance, SEC EDGAR, Reddit/RSS, Google Gemini.

---

## Quick start

1. **Clone and env**

   ```bash
   git clone git@github.com:adhanraj06/PreTerm.git
   cd PreTerm
   cp .env.example .env
   ```

2. **Install** (creates `backend/venv`, installs Python + npm deps)

   ```bash
   make install
   ```

3. **Run** (backend + frontend together)

   ```bash
   make run
   ```

4. **Open**

   - App: [http://localhost:5173](http://localhost:5173)
   - API health: [http://localhost:8000/api/health](http://localhost:8000/api/health)

**Demo login** (when `SEED_DEMO_USER` is true, see `.env.example`): e.g. `demo@preterm.local` / `demo12345`.

Other useful targets: `make backend`, `make frontend`, `make build-frontend`, `make clean`, `make reset`. See the [Makefile](Makefile) for the full list.

---

## Repository layout

```text
backend/app/     # FastAPI app: api/, services/, models/, integrations/, db/
frontend/src/    # React: app/, features/, components/, api/, types/
docs/            # Documentation (see below)
scripts/         # venv, install, run, bootstrap, clean, reset
fred.csv         # Optional wide monthly macro table for FRED-offline mode
```

---

## Configuration

- **Environment:** Copy [.env.example](.env.example) to `.env` and adjust. Secrets (JWT, API keys) stay out of git (see [.gitignore](.gitignore)).
- **Kalshi:** Set `MARKET_DATA_PROVIDER=kalshi` when you want live markets; use `seeded` or rely on `KALSHI_FALLBACK_TO_SEEDED=true` for resilient demos.
- **Macro:** Set `FRED_API_KEY` for the live FRED API, or rely on `fred.csv` at the repo root / `FRED_CSV_PATH`.
- **Copilot / brief LLM:** `GEMINI_API_KEY` and optional `KALSHI_BRIEF_USE_GEMINI`.

Detailed matrices live in [docs/SETUP.md](docs/SETUP.md) and [docs/DEV.md](docs/DEV.md) (Part II).

---

## Documentation

| Doc | Audience |
|-----|----------|
| [docs/DEMO.md](docs/DEMO.md) | **Product:** every page, control, flow, demo script, FAQ. |
| [docs/DEV.md](docs/DEV.md) | **Product + engineering:** same product depth as DEMO, plus APIs, data model, integrations, ops. |
| [docs/SETUP.md](docs/SETUP.md) | Environment and verification steps. |
| [docs/VERCEL.md](docs/VERCEL.md) | Deploy on Vercel (multi-service: Vite + FastAPI). |

---

## Deployment notes

- **Vercel (frontend + FastAPI):** See [docs/VERCEL.md](docs/VERCEL.md). Root [`vercel.json`](vercel.json) defines **Vite** at `/` and **FastAPI** at `/_/backend`. Use **PostgreSQL** for `DATABASE_URL` (not SQLite on serverless).
- **ASGI:** [backend/app/asgi.py](backend/app/asgi.py); production helper: `make backend-prod`.
- **Docker:** [Dockerfile](Dockerfile) in repo root.
- **Single host:** build the SPA (`make build-frontend`), set `SERVE_FRONTEND=true` and `FRONTEND_DIST_DIR` so FastAPI can serve static assets alongside `/api`.

---

## License

Add a `LICENSE` file if you intend open-source distribution; none is bundled by default in this snapshot.

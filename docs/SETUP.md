# PreTerm Setup Guide

This guide is the final setup reference for local development, final demo prep, and eventual deployment planning.

The goal is simple:

- get the repo running locally
- decide whether to demo with seeded or live enrichments
- verify every major subsystem before presentation
- recover quickly if an integration fails

## 1. Required Software

Install all of the following before doing anything else:

- `Python 3.11+`
  - check with `python3 --version`
- `Node.js 20+`
  - check with `node --version`
- `npm`
  - check with `npm --version`
- `make`
  - check with `make --version`

Recommended but not strictly required:

- `curl`
  - useful for quick backend verification
- `git`
  - for normal source control workflow

## 2. Repo Files You Should Know

- root env template: `.env.example`
- local env file you create: `.env`
- main project overview: `README.md`
- final demo script: `docs/DEMO.md`
- developer workflow entrypoint: `Makefile`

## 3. Local Install Steps

From the repo root:

1. Create the local env file:

```bash
cp .env.example .env
```

2. Review `.env` before installing anything.

3. Create the Python virtual environment:

```bash
make venv
```

4. Install backend and frontend dependencies:

```bash
make install
```

5. Start the full app:

```bash
make run
```

Expected local URLs:

- frontend: `http://localhost:5173`
- backend: `http://localhost:8000`
- health check: `http://localhost:8000/api/health`

## 4. Environment File Setup

All environment variables live in the root `.env`.

Create it once:

```bash
cp .env.example .env
```

Do not put secrets inside frontend source files.

## 5. Environment Variable Matrix

### Required for local app startup

- `APP_ENV`
  - recommended local value: `development`
- `DATABASE_URL`
  - local default: `sqlite:///./preterm.db`
- `JWT_SECRET`
  - set a nontrivial value for real deployment
  - local demo can use a simple value
- `BACKEND_HOST`
  - local default: `0.0.0.0`
- `BACKEND_PORT`
  - local default: `8000`
- `API_V1_PREFIX`
  - local default: `/api`
- `CORS_ORIGINS`
  - local default: `http://localhost:5173,http://127.0.0.1:5173`
- `FRONTEND_HOST`
  - local default: `0.0.0.0`
- `FRONTEND_PORT`
  - local default: `5173`
- `VITE_API_URL`
  - local default: `http://localhost:8000`

### Required for production-friendly backend startup

- `APP_HOST`
  - backend production bind host
  - default: `0.0.0.0`
- `APP_PORT`
  - backend production bind port
  - default: `8000`
- `APP_RELOAD`
  - local dev convenience
  - default: `true`
- `APP_WORKERS`
  - production-friendly worker count
  - default: `1`
- `LOG_LEVEL`
  - default: `info`
- `SERVE_FRONTEND`
  - if `true`, FastAPI can serve the built frontend
  - useful for single-container deployment
- `FRONTEND_DIST_DIR`
  - default: `../frontend/dist`

### Required API keys

Strictly speaking, none are required for the deterministic seeded demo path.

If you want the richest live demo, the most important optional key is:

- `GEMINI_API_KEY`
  - used for the market copilot

### Optional API keys

- `GEMINI_API_KEY`
  - used for the context-aware copilot
- `FRED_API_KEY`
  - used for macro context

### Optional integration flags

- `MARKET_DATA_PROVIDER`
  - `seeded` or `kalshi`
  - recommended default: `seeded`
- `MARKET_DATA_REFRESH_SECONDS`
  - Kalshi refresh interval
- `KALSHI_API_BASE`
  - default: `https://api.elections.kalshi.com/trade-api/v2`
- `KALSHI_MARKET_LIMIT`
  - recommended default: `18`
- `KALSHI_MARKET_STATUS`
  - recommended default: `open`
- `KALSHI_SERIES_FILTER`
  - optional comma-separated series filter
- `KALSHI_FALLBACK_TO_SEEDED`
  - recommended default: `true`
- `KALSHI_REQUEST_TIMEOUT_SECONDS`
  - recommended default: `10`
- `FRED_API_BASE`
  - default: `https://api.stlouisfed.org/fred`
- `ENABLE_YFINANCE`
  - recommended default: `true`
- `ENABLE_EDGAR`
  - recommended default: `true`
- `SEC_DATA_API_BASE`
  - default: `https://data.sec.gov`
- `SEC_USER_AGENT`
  - use a real contact string
- `GEMINI_MODEL`
  - default: `gemini-1.5-flash`
- `VITE_BASE_PATH`
  - useful later for subpath deployment

### Fallback-safe values

These can be left blank or disabled without breaking the app:

- `GEMINI_API_KEY`
- `FRED_API_KEY`
- `KALSHI_SERIES_FILTER`

These can remain enabled even if the live provider fails, because the app degrades gracefully:

- `ENABLE_YFINANCE=true`
- `ENABLE_EDGAR=true`
- `KALSHI_FALLBACK_TO_SEEDED=true`

## 6. How to Get Each API Key

### Gemini

- Go to Google AI Studio
- create or use an existing project
- generate an API key
- put it in `.env` as:

```bash
GEMINI_API_KEY=your_key_here
```

### FRED

- Go to the Federal Reserve Economic Data API page
- request an API key
- put it in `.env` as:

```bash
FRED_API_KEY=your_key_here
```

### Kalshi

- no API key is required for the current public market metadata flow
- you only need:

```bash
MARKET_DATA_PROVIDER=kalshi
```

### SEC EDGAR

- no API key is required
- but you should set a polite user agent:

```bash
SEC_USER_AGENT=PreTerm/0.1 your-email@example.com
```

### NLTK / VADER

- no API key is required
- the lexicon is downloaded automatically on first startup if needed

## 7. How to Run Locally

### Create the virtual environment

```bash
make venv
```

### Install everything

```bash
make install
```

### Start the full app

```bash
make run
```

### Start only the backend

```bash
make backend
```

### Start only the frontend

```bash
make frontend
```

### Build the frontend for deployment testing

```bash
make build-frontend
```

### Run the backend in a more production-like mode

```bash
make backend-prod
```

## 8. How to Switch Seeded vs Live Modes

### Deterministic seeded mode

This is the safest demo path.

Use:

```bash
MARKET_DATA_PROVIDER=seeded
```

Recommended with:

```bash
KALSHI_FALLBACK_TO_SEEDED=true
```

### Kalshi-backed mode

Use:

```bash
MARKET_DATA_PROVIDER=kalshi
KALSHI_FALLBACK_TO_SEEDED=true
```

Optional:

```bash
KALSHI_SERIES_FILTER=
```

If Kalshi fails, the app should fall back cleanly when `KALSHI_FALLBACK_TO_SEEDED=true`.

### Macro live mode

Add:

```bash
FRED_API_KEY=your_key_here
```

If omitted, macro panels show an unavailable state instead of breaking.

### Copilot live mode

Add:

```bash
GEMINI_API_KEY=your_key_here
```

If omitted, the copilot uses deterministic mock responses.

## 9. Subsystem Verification Checklist

Run this after `make run`.

### Auth

Verify:

- app opens to login
- demo credentials are prefilled
- login succeeds
- refresh keeps the session
- logout works

Optional API check:

```bash
curl http://localhost:8000/api/health
```

### Markets

Verify:

- `/app/monitor` loads
- markets list is visible
- selecting a market updates the detail panel
- selected row is visibly highlighted

### Watchlists

Verify:

- create a watchlist
- add the selected market
- remove an item
- save a view
- reopen a saved view

### Event Brief

Verify:

- selected market shows:
  - summary
  - why this matters now
  - what changed
  - bull / base / bear framing
- move timeline renders
- historical chart renders

### Headline Map

Verify:

- go to `/app/headlines`
- run a sample headline
- top matched market appears
- “Open Matched Market Brief” jumps correctly into monitor

### Copilot

Verify:

- right-side copilot panel is visible
- starter prompts work
- response references the selected market

If `GEMINI_API_KEY` is missing:

- confirm the mock response path still works

### Kalshi Provider

Only if using live mode.

Verify:

- set `MARKET_DATA_PROVIDER=kalshi`
- restart with `make run`
- markets still load
- at least one market shows `source: kalshi` through the backend payload if inspected
- market detail still opens with snapshots and brief

### FRED Integration

Only if using `FRED_API_KEY`.

Verify:

- open a macro market
- compact macro context panel appears
- at least one series chart renders

If no key:

- confirm the panel degrades gracefully

### Sentiment Layer

Verify:

- open `/app/headlines`
- switch to `Sentiment`
- paste text
- receive:
  - compound score
  - bullish / bearish / neutral label
  - matched market if relevant

Optional URL verification:

- use a public article or Reddit URL
- confirm extraction works or returns a clean fallback note

### Finance Context

Verify:

- open a mapped market such as Nvidia, Tesla, Amazon, S&P 500, or Bitcoin
- confirm the company / asset context panel appears only when relevant
- if unavailable, confirm it hides cleanly

### Planner

Verify:

- open `/app/planner`
- create a planned event
- suggested markets appear
- clicking a suggested market jumps into `/app/monitor`

## 10. How to Test Seeded Fallback Mode

This is the preferred final-demo safety path.

Set:

```bash
MARKET_DATA_PROVIDER=seeded
GEMINI_API_KEY=
FRED_API_KEY=
KALSHI_FALLBACK_TO_SEEDED=true
```

Then:

```bash
make run
```

Verify:

- monitor works
- event briefs work
- headline map works
- watchlists and saved views work
- planner works
- copilot still answers in mock mode
- sentiment still works for pasted text

## 11. Demo-Day Checklist

Use this in order.

1. Confirm `.env` is the exact version you want for the demo.
2. Decide whether the demo is:
   - fully deterministic seeded
   - seeded + Gemini
   - seeded + Gemini + FRED
   - Kalshi + fallback-safe
3. Run:

```bash
make reinstall
make run
```

4. Log in once before presenting.
5. Open these routes and make sure each loads:
   - `/app/monitor`
   - `/app/watchlists`
   - `/app/headlines`
   - `/app/planner`
   - `/app/settings`
6. Confirm the selected market experience looks good on the monitor route.
7. Run one headline map query.
8. Run one copilot prompt.
9. Confirm planner suggestions work.
10. Keep `docs/DEMO.md` open during final prep.

## 12. Troubleshooting

### `make install` fails

Check:

- Python is installed
- Node and npm are installed
- network access is available

Then run:

```bash
make reinstall
```

### Backend virtual environment missing

Run:

```bash
make venv
make install
```

### Frontend dependencies missing

Run:

```bash
make install
```

### Backend starts but auth behaves oddly

Check:

- `JWT_SECRET` exists in `.env`
- stale frontend token is cleared by logging out and back in
- backend is using the current database file

If needed:

```bash
make reset
make install
make run
```

### Port `8000` or `5173` is already in use

Update `.env`:

- `BACKEND_PORT`
- `FRONTEND_PORT`
- `VITE_API_URL` if backend port changes

Restart:

```bash
make run
```

### Frontend cannot reach backend

Check:

- backend terminal is still running
- `curl http://localhost:8000/api/health` works
- `VITE_API_URL` is correct
- `CORS_ORIGINS` includes the frontend origin

### Kalshi mode fails or returns no useful markets

Check:

- `MARKET_DATA_PROVIDER=kalshi`
- `KALSHI_API_BASE=https://api.elections.kalshi.com/trade-api/v2`
- `KALSHI_FALLBACK_TO_SEEDED=true`

If still unstable, switch back:

```bash
MARKET_DATA_PROVIDER=seeded
```

### FRED macro context is unavailable

Check:

- `FRED_API_KEY` is set
- `FRED_API_BASE` is correct
- selected market is truly macro-linked

If still failing, demo the unavailable state and continue.

### Copilot falls back unexpectedly

Check:

- `GEMINI_API_KEY` is set
- internet access works

If Gemini is unavailable, continue the demo with the deterministic copilot path.

### Sentiment analysis unavailable on first startup

Check:

- `make install` completed
- backend restarted at least once
- machine had network access the first time VADER tried to download

If URL extraction fails, use pasted text instead.

### Finance context does not appear

Check:

- `ENABLE_YFINANCE=true`
- `ENABLE_EDGAR=true` for company-linked markets
- `SEC_USER_AGENT` is set
- the selected market is one of the mapped finance-context markets

If the integration fails, the panel should hide cleanly.

### Planner suggestions look weak

Use a more specific event:

- add a stronger concern type
- add clearer notes
- reference the type of risk more explicitly

## 13. Production-Oriented Notes

PreTerm is still local-first, but the repo is now cleaner for later deployment.

Available paths:

- `make backend-prod`
  - runs the backend against `app.asgi:app`
- `make build-frontend`
  - produces `frontend/dist`
- root `Dockerfile`
  - builds frontend
  - installs backend
  - optionally serves built frontend through FastAPI when `SERVE_FRONTEND=true`

Recommended posture for the final project:

- develop locally in seeded mode
- enable live integrations only if you are confident in the demo environment
- always keep a deterministic fallback path ready

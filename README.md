# PreTerm

PreTerm is a personalized prediction-market workstation. It extends the original PreTerm MVP by preserving the three original pillars, then adding persistent user workflows, deeper event interpretation, and market-aware planning support in one cohesive product.

## What PreTerm Does

PreTerm is built around three core product surfaces:

- `Market Monitor`
  - browse active contracts
  - inspect current probability, recent move, and status
  - pin important markets into the desk
- `Event Brief`
  - explain why a market matters now
  - structure bull / base / bear framing
  - connect price moves to timeline entries, headlines, and macro context
- `Headline Map`
  - map incoming news into the most relevant market
  - explain directional impact and why the event matters

The final product adds:

- authenticated user profiles
- watchlists and saved views
- alert preferences and notifications
- market copilot with Gemini fallback behavior
- Kalshi-backed market data with seeded fallback
- FRED macro context
- optional company / asset context
- in-app hedge planner for real-world events

## Stack

- Backend: `FastAPI`
- Frontend: `React + Vite + TypeScript`
- Database: `SQLite` for local development
- Python env: `backend/venv`
- Root developer interface: `Makefile`

## Repo Layout

- `backend/`
  - API, services, models, integrations, database setup
- `frontend/`
  - React app, workstation UI, routes, styles
- `docs/`
  - final prep and demo documentation
- `scripts/`
  - local dev helpers

## Local Development

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Install backend and frontend dependencies:

```bash
make install
```

3. Start the app:

```bash
make run
```

Default local URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health check: `http://localhost:8000/api/health`

Useful commands:

- `make venv`
- `make install`
- `make backend`
- `make frontend`
- `make run`
- `make build-frontend`
- `make backend-prod`
- `make clean`
- `make reset`
- `make reinstall`

## Deployment Readiness

The repo stays local-first, but it now has a cleaner path toward deployment:

- environment-driven backend settings
- ASGI entrypoint at `backend/app/asgi.py`
- production backend runner via `make backend-prod`
- Vite config supports env-driven host, port, and base path
- optional root `Dockerfile` for a single-container deployment path
- optional static frontend serving from the FastAPI app when `SERVE_FRONTEND=true`

This is still optimized for local development, but the structure is clean enough to move toward:

- a single Docker deployment
- split frontend/backend deployment
- Postgres later if SQLite becomes limiting

## Environment Variables

See `docs/SETUP.md` for the detailed matrix. At a high level:

- always review `.env`
- keep `MARKET_DATA_PROVIDER=seeded` for deterministic local work
- add only the API keys you need for the demo you plan to give

## Documentation

- Setup and verification: `docs/SETUP.md`
- Full final demo script: `docs/DEMO.md`

## Current Status

PreTerm is structured as a final-project-ready demo application:

- strong local development workflow
- polished workstation UI
- deterministic fallback paths for live integrations
- detailed setup and demo prep docs

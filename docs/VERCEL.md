# Deploy PreTerm on Vercel (frontend + FastAPI)

Vercel can run this repo as **two Web Services** in one project: a **Vite** frontend at `/` and a **FastAPI** backend at `/_/backend`. Routing is defined in the root [`vercel.json`](../vercel.json).

---

## 1. Prerequisites

- GitHub repo connected (e.g. `adhanraj06/PreTerm`).
- Vercel account; **CLI ≥ 48.1.8** if you use `vercel dev` locally.
- **Important:** Use a hosted **PostgreSQL** (e.g. [Neon](https://neon.tech), [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres)) and set **`DATABASE_URL`** in the Vercel project. The app normalizes `postgresql://` and `postgres://` to **`postgresql+psycopg2://`** automatically. If **`DATABASE_URL` is not set** on Vercel, the API falls back to **`sqlite:////tmp/preterm.db`** (writable, but **ephemeral**—data is lost across cold starts). A checked-in local `.env` is **not** deployed, so production usually does not inherit `sqlite:///./preterm.db` from your laptop.

---

## 2. Import the project

1. **New Project** → import `adhanraj06/PreTerm` (branch `main`).
2. **Root Directory:** `./` (repository root).
3. Vercel should detect **`vercel.json`** and show **two services** (Vite + FastAPI), matching the dashboard you described.
4. **Project name:** e.g. `pre-term`.

If the UI says **`vercel.json` required**, commit and push the [`vercel.json`](../vercel.json) from this repo, then reconnect or redeploy.

---

## 3. Environment variables (Project → Settings → Environment Variables)

Set these for **Production** (and **Preview** if you want previews to work the same).

### Required

| Variable | Example / notes |
|----------|------------------|
| `DATABASE_URL` | `postgresql+psycopg2://USER:PASS@HOST/DB?sslmode=require` (Neon / Vercel Postgres) |
| `JWT_SECRET` | Long random string (not `change-me`) |

### Strongly recommended

| Variable | Notes |
|----------|--------|
| `CORS_ORIGINS` | Your site origin(s), e.g. `https://pre-term-xxx.vercel.app` — needed if you ever call the API from a **different** origin. With the default setup, the browser uses **same-origin** URLs (`/_/backend/...`), so CORS is often unnecessary. |
| `MARKET_DATA_PROVIDER` | `seeded` for a stable demo without Kalshi; or `kalshi` if you accept rate limits / cold-start latency. |
| `FRED_API_KEY` | Only if you need live FRED (else bundle `fred.csv` in repo for CSV mode). |
| `GEMINI_API_KEY` | Optional Copilot / brief enrichment. |

### Frontend build (`VITE_*`)

Vercel injects build env for the **frontend** service. Optional override:

| Variable | Value |
|----------|--------|
| `VITE_API_URL` | `/_/backend` |

If you omit it, the frontend **production** build defaults to `/_/backend` (see `frontend/src/api/client.ts`).

### Copy from local template

Use [`.env.example`](../.env.example) as a checklist. **Do not** commit real secrets.

---

## 4. How routing works

| User / browser | Service |
|----------------|---------|
| `https://<deployment>/` and SPA routes | **frontend** (Vite static + client routing) |
| `https://<deployment>/_/backend/api/...` | **backend** (FastAPI) |

The frontend calls `fetch("/_/backend" + "/api/health")` → `/_/backend/api/health` on the **same** deployment hostname, so requests are **same-origin** (no CORS preflight for simple cases).

Vercel’s Python runtime may strip the service `routePrefix` before your app sees the path, or set ASGI `root_path`; your routes stay **`/api/...`** inside FastAPI.

---

## 5. Backend entrypoint

The backend service root is the [`backend/`](../backend/) folder. Vercel looks for a FastAPI `app` in standard filenames; this repo exposes it via [`backend/index.py`](../backend/index.py):

```python
from app.main import app
```

---

## 6. First deploy checklist

- [ ] `vercel.json` present at repo root.
- [ ] `DATABASE_URL` points to **Postgres** (not SQLite on Vercel).
- [ ] `JWT_SECRET` set.
- [ ] Redeploy after changing env vars (Vercel rebuilds as needed).
- [ ] Open `https://<your-deployment>/api/health` **under the backend prefix**:  `https://<your-deployment>/_/backend/api/health` → should return `{"ok": true}`.

---

## 7. Limitations and tips

- **Cold starts:** First request after idle can be slow; Kalshi refresh in app **lifespan** may add latency or hit **429** — use `MARKET_DATA_PROVIDER=seeded` for demos.
- **File uploads / SQLite:** Avoid SQLite in production on Vercel.
- **`fred.csv`:** Included in the repo; ensure the deployment bundle includes it if you rely on CSV macro mode without `FRED_API_KEY`.
- **NLTK / VADER:** `ensure_vader_ready()` may download data on cold start; keep an eye on logs and timeouts.
- **Custom domain:** After adding a domain, if you use strict `CORS_ORIGINS`, add the new origin.

---

## 8. Alternative: frontend-only on Vercel

If you do **not** want to run Python on Vercel, deploy only the **static** frontend (or another host) and set:

`VITE_API_URL=https://your-api.railway.app` (or Fly.io, Render, etc.)

Run the FastAPI stack from [`Dockerfile`](../Dockerfile) or `uvicorn` on a VM-friendly platform. SQLite is fine there if a persistent volume is attached.

---

## 9. References

- [Vercel — Services routing](https://vercel.com/docs/services/routing)
- [Vercel — FastAPI](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel CLI](https://vercel.com/docs/cli)

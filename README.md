# Landslide Risk Dashboard

A FastAPI backend + dashboard that ranks Indian states/regions by landslide
risk, combining rainfall-excess data with terrain susceptibility.

## How the risk model works

Landslide risk here is **not** just "more rain = more risk." It combines two
factors:

1. **Rainfall excess** — how far actual rainfall is above/below the normal
   for that region (a large surplus is the usual landslide trigger).
2. **Terrain susceptibility** — a static score per state based on known
   geology/slope (Himalayan states, the Western Ghats, and NE hill states
   score highest; flat plains score lowest). See
   `backend/terrain_susceptibility.py`.

These combine into a 0–100 risk score and a Low / Moderate / High / Very High
label. See `backend/risk_model.py` for the exact formula and comments.

This starts as a transparent **rule-based** model (no training data needed,
works immediately). If you later get access to real historical landslide
event records (e.g. from GSI Bhukosh or NRSC's landslide inventory), you can
call `train_model()` in `risk_model.py` to fit a proper logistic regression
instead — the API automatically switches to using it once `trained_model.pkl`
exists.

## Data source — important

`mausam.imd.gov.in`'s rainfall pages load their numbers via JavaScript after
the page loads, so they can't be scraped with a simple HTTP request. Two
options are wired up:

- **CSV-based (works today):** `backend/data/rainfall_data.csv`. Edit it
  directly, or upload a new one via the dashboard's upload button, or POST to
  `/api/rainfall`.
- **Live IMD scraping (not yet wired up):** see the detailed instructions in
  `backend/data_source.py` — it walks through finding the real data endpoint
  using your browser's Developer Tools (Network tab), which takes about two
  minutes. Once you have that URL, send it my way and I'll wire up
  `fetch_from_imd()` to call it directly.

## Running locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/` in a browser.

## API endpoints

- `GET /api/rainfall` — raw rainfall data currently loaded
- `GET /api/risk` — rainfall data run through the risk model, ranked
- `POST /api/rainfall` — replace dataset (JSON body)
- `POST /api/upload-csv` — replace dataset (CSV file upload)

## Deploying it live

GitHub Pages **cannot** host this — it only serves static files, and this
needs a Python process running continuously. Use a free-tier host that runs
Python instead:

### Option A: Render (recommended, simplest)
1. Push this whole folder to a GitHub repo.
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo.
3. Root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Deploy — Render gives you a live URL like `https://your-app.onrender.com`

### Option B: Railway
Same idea as Render — connect the GitHub repo, set the root to `backend`,
and use the same start command.

Either way, keeping this running "constantly" (as in continuously
re-checking data) on a free tier means adding a scheduled job (e.g. a
lightweight cron endpoint, or Render's built-in Cron Jobs feature) that
calls your data-refresh logic every few hours — free tiers spin down when
idle, so true 24/7 background polling needs a paid tier or an external
scheduler (like a GitHub Action) hitting a `/refresh` endpoint periodically.
# landslide

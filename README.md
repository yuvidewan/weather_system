# Probabilistic Weather Expert System

Full-stack expert system that predicts rainfall and weather conditions using:
- Data intelligence layer (live ingestion fallback, baseline biasing, sensor reliability, imputation)
- Hybrid probabilistic engine (priors + dynamic transitions + calibration + expert rules)
- Forecast depth (multi-horizon projections, event timing probabilities, intensity bands)
- Explainability (rule trace, attribution, counterfactuals, expert narrative)
- Decision support (risk profiles, threshold policies, recommendations)
- Geo comparison (multi-location endpoint)
- Enterprise support basics (API key auth, roles, SQLite forecast history + audit log)

## Project Structure

```text
expert_system/
  backend/
    app/
      config.py
      knowledge_base.py
      probabilistic_engine.py
      schemas.py
      main.py
    requirements.txt
    .env.example
  frontend/
    index.html
    styles.css
    app.js
  .gitignore
  README.md
```

## Feature Set

- Expanded knowledge base with seasonal, terrain, climate-zone, and monthly multipliers
- Larger expert rule library (multiple rain/fog/storm/clear/windy triggers)
- Multi-horizon forecasts (`1h`, `3h`, `6h`, `12h`, `24h`)
- Scenario outputs (`best_case`, `expected_case`, `worst_case`)
- Event outputs (`rain_onset_within_3h`, `storm_onset_within_6h`, `heavy_rain_within_12h`)
- Intensity band probabilities (`light`, `moderate`, `heavy`, `extreme`)
- Risk mode profiles (`general`, `agriculture`, `travel`, `events`, `logistics`)
- Persistent history and audit storage in SQLite
- Forecast verification + calibration tracking (`/api/v1/outcome`, `/api/v1/calibration`)
- Alert subscriptions + notification log (webhook/email/sms/log channels)
- History filtering + analytics endpoints
- Async batch forecast jobs
- Runtime knowledge-base version snapshots + activation
- Multi-provider live weather ingestion with cache
- Large synthetic climatology dataset for low-weight prior smoothing (variance control, not direct fitting)
- Professional frontend command console with advanced visual panels

## Backend Setup (Python)

1. Open terminal:
```powershell
cd c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend
```

2. Create and activate virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Create env file:
```powershell
Copy-Item .env.example .env
```

5. Run API:
```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs:
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

Auth headers for protected endpoints:
- `x-api-key: dev-admin-key` (or `dev-analyst-key`)
- `x-role: admin|analyst|viewer`

## Frontend Setup

Run a static server from `frontend`:

```powershell
cd c:\Users\yuvra\Desktop\PROJECTS\expert_system\frontend
python -m http.server 5500
```

Open:
- `http://127.0.0.1:5500`

By default, UI points to `http://127.0.0.1:8000`.

## Main API Endpoints

- `POST /api/v1/infer`
  - Full inference with scenarios, horizons, event probabilities, explainability, data quality
- `POST /api/v1/infer/multi-location`
  - Compare risk across up to 10 locations for the same observation
- `GET /api/v1/live-weather?lat=<>&lon=<>`
  - Optional live ingestion endpoint with deterministic fallback
- `GET /api/v1/knowledge-base`
  - Returns priors and expanded multipliers/thresholds used by the expert system
- `GET /api/v1/history`
  - Returns persisted forecast history
- `GET /api/v1/history/analytics`
  - Aggregate forecast metrics, timeline, and location-level rollups
- `POST /api/v1/outcome`
  - Submit observed outcomes and compute Brier score
- `GET /api/v1/calibration`
  - Calibration and reliability-bin summaries
- `POST /api/v1/alerts/subscriptions`
  - Create alert subscriptions
- `GET /api/v1/alerts/subscriptions`
  - List subscriptions
- `GET /api/v1/alerts/notifications`
  - Notification delivery log
- `POST /api/v1/jobs/forecast-batch`
  - Async multi-location forecast job
- `GET /api/v1/jobs/forecast-batch`
  - List batch jobs
- `GET /api/v1/jobs/forecast-batch/{job_id}`
  - Inspect one batch job
- `GET /api/v1/dataset/stats`
  - Climatology dataset metadata
- `GET /api/v1/knowledge-base/versions`
  - List KB snapshots
- `POST /api/v1/knowledge-base/versions`
  - Create KB snapshot
- `POST /api/v1/knowledge-base/versions/{id}/activate`
  - Activate KB snapshot
- `GET /health`

## Example Inference Request

```json
{
  "location": "Mumbai",
  "horizon_hours": 6,
  "risk_mode": "events",
  "custom_thresholds": {
    "high": 0.5
  },
  "observation": {
    "temperature_c": 30.5,
    "humidity_pct": 84,
    "pressure_hpa": 998,
    "wind_kph": 24,
    "cloud_cover_pct": 86,
    "dew_point_c": 27,
    "recent_rain_mm": 7.2,
    "uv_index": 4,
    "visibility_km": 6,
    "month": 7,
    "hour_24": 17,
    "season": "monsoon",
    "terrain": "coastal",
    "pressure_trend": "falling",
    "source_confidence": {
      "manual": 0.8,
      "station": 0.88,
      "satellite": 0.83,
      "radar": 0.9,
      "model": 0.79
    }
  }
}
```

## Notes

- This is a rule-augmented probabilistic expert system intended for decision support and educational use.
- It is not a substitute for official meteorological warnings.

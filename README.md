# Probabilistic Weather Expert System

Full-stack expert system that predicts rainfall and weather conditions using:
- Probabilistic reasoning (Bayesian-style scoring + softmax normalization)
- Expert rule engine (domain rules for pressure, humidity, fog, convection, wind)
- Monte Carlo rainfall expectation simulation
- Explainability outputs (key factors + natural-language explanation)
- Risk/alert interpretation and recommendations

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

- Inference API endpoint with typed validation
- Weather condition probability vector:
  - `clear`, `cloudy`, `rain`, `drizzle`, `thunderstorm`, `fog`, `windy`
- Aggregated rain probability over selected forecast horizon
- Expected rainfall amount (mm) from stochastic simulation
- Confidence score from prediction entropy
- Alert levels: `low`, `moderate`, `high`, `severe`
- Top factor impacts for explainability
- Human-readable expert explanation
- Recent in-memory inference history endpoint
- Web dashboard to input meteorological signals and visualize results

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
  - Input: location + observation object + horizon
  - Output: complete inference package with probabilities, rainfall estimate, alerts, recommendations, factors
- `GET /api/v1/knowledge-base`
  - Returns priors and multipliers used by the expert system
- `GET /api/v1/history`
  - Returns recent inference summaries
- `GET /health`

## Example Inference Request

```json
{
  "location": "Mumbai",
  "horizon_hours": 6,
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
    "pressure_trend": "falling"
  }
}
```

## Notes

- This is a rule-augmented probabilistic expert system intended for decision support and educational use.
- It is not a substitute for official meteorological warnings.


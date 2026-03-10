
# Expert System Viva Guide

Updated for the current codebase after the latest pull.

## 1. Project Summary

This project is a full-stack probabilistic weather expert system. It predicts likely weather conditions, rain probability, expected rainfall, alert level, event windows, scenario outputs, and decision recommendations from a structured weather observation.

The system is hybrid, not purely rule-based and not purely machine learning.

It combines:

- expert knowledge encoded in Python
- probabilistic scoring and normalization
- contextual multipliers for season, terrain, climate zone, and month
- reliability-aware calibration
- low-weight climatology smoothing from a synthetic historical dataset
- persistence, analytics, subscriptions, and audit logging in SQLite

Current backend version in the code is `2.0.0` in [main.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L50).

## 2. Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- Uvicorn
- SQLite using built-in `sqlite3`
- `python-dotenv`
- standard library threading for async-style background jobs

### Frontend

- plain HTML
- plain CSS
- plain JavaScript
- no frontend framework

## 3. Main Architectural Idea

This project has 5 practical layers.

### Layer 1. UI layer

The frontend collects inputs, calls the API, and visualizes results such as:

- condition probabilities
- intensity bands
- event probabilities
- multi-horizon outputs
- city heatmaps
- India spatial heatmap

### Layer 2. API orchestration layer

FastAPI routes in [main.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py) do request validation, security checks, orchestration, persistence, and response shaping.

### Layer 3. Inference layer

The core forecast logic is in [probabilistic_engine.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py).

### Layer 4. Knowledge layer

Knowledge is defined in:

- [knowledge_base.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\knowledge_base.py)
- [runtime_knowledge.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\runtime_knowledge.py)
- [climatology_dataset.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py)

### Layer 5. Persistence and support services

Operational storage and support features are in:

- [storage.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py)
- [alerts.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\alerts.py)
- [weather_provider.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py)
- [batch_jobs.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\batch_jobs.py)

## 4. What Type of Expert System This Is

Best viva answer:

This is a hybrid probabilistic expert system for weather reasoning.

Why hybrid:

- It has explicit expert rules.
- It has hand-crafted domain priors and multipliers.
- It converts evidence into condition scores and then probabilities.
- It adds context-sensitive and reliability-sensitive adjustments.
- It produces explainable outputs instead of only one label.

Why it is not a pure ML system:

- no training loop
- no learned model weights from real historical labeled training data
- no neural network
- no sklearn model

Why it is not only a classic IF-THEN rule engine:

- rules do not directly decide the output
- rules only contribute weighted evidence into a probabilistic pipeline
- final output is normalized over multiple competing conditions

## 5. Current Project Structure

```text
expert_system/
  backend/
    app/
      __init__.py
      alerts.py
      batch_jobs.py
      climatology_dataset.py
      config.py
      data_intelligence.py
      knowledge_base.py
      main.py
      probabilistic_engine.py
      runtime_knowledge.py
      schemas.py
      security.py
      storage.py
      weather_provider.py
  frontend/
    index.html
    app.js
    styles.css
  README.md
  PROJECT_VIVA_GUIDE.md
```

## 6. Startup Flow

Main startup happens in [main.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py).

Execution flow:

1. `settings` is loaded from [config.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\config.py).
2. FastAPI app is created at [main.py:50](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L50).
3. CORS middleware is added at [main.py:56](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L56).
4. `init_db()` is called at [main.py:64](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L64).
5. SQLite tables are created if they do not exist.
6. API endpoints become available.

Important point:

Database setup is done during app startup, not on first request.

## 7. Configuration

The configuration file is [config.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\config.py).

It provides:

- app name
- app environment
- app port
- comma-separated CORS origins

Live weather behavior also depends on environment variables read inside [weather_provider.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py):

- `LIVE_PROVIDER_TIMEOUT_SEC`
- `LIVE_CACHE_TTL_SEC`

## 8. Security Model

Security is implemented in [security.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\security.py#L15).

It uses header-based API key authorization.

Headers:

- `x-api-key`
- `x-role`

Default keys:

- `dev-admin-key`
- `dev-analyst-key`

Role mapping:

- admin key maps to `admin`
- analyst key maps to `analyst`

Rules:

1. invalid key returns `401`
2. allowed roles are only `admin`, `analyst`, `viewer`
3. non-admin keys cannot claim admin role

Important viva point:

This is lightweight role validation, not a full production RBAC design.

## 9. Current API Endpoints

Defined in [main.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py).

### Core system endpoints

- `GET /health`
- `GET /api/v1/knowledge-base`
- `GET /api/v1/knowledge-base/active`
- `GET /api/v1/knowledge-base/versions`
- `POST /api/v1/knowledge-base/versions`
- `POST /api/v1/knowledge-base/versions/{version_id}/activate`

### Forecast endpoints

- `POST /api/v1/infer`
- `POST /api/v1/infer/multi-location`
- `POST /api/v1/jobs/forecast-batch`
- `GET /api/v1/jobs/forecast-batch`
- `GET /api/v1/jobs/forecast-batch/{job_id}`

### Data and live ingestion endpoints

- `GET /api/v1/live-weather`
- `GET /api/v1/dataset/stats`

### Persistence and analytics endpoints

- `GET /api/v1/history`
- `GET /api/v1/history/analytics`
- `POST /api/v1/outcome`
- `GET /api/v1/calibration`

### Alerting endpoints

- `POST /api/v1/alerts/subscriptions`
- `GET /api/v1/alerts/subscriptions`
- `POST /api/v1/alerts/subscriptions/{subscription_id}/toggle`
- `GET /api/v1/alerts/notifications`

## 10. Pydantic Schemas

Schemas are in [schemas.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\schemas.py).

Main models:

- `WeatherObservation`
- `InferenceRequest`
- `InferenceResponse`
- `MultiLocationRequest`
- `MultiLocationResponse`
- `OutcomeReportRequest`
- `AlertSubscriptionRequest`
- `BatchJobRequest`
- `KnowledgeBaseVersionCreateRequest`

New important schema addition:

`InferenceResponse` now includes `climatology_meta` at [schemas.py:102](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\schemas.py#L102), which tells you which city climatology was used, how many records were blended, and what blend alpha was applied.

Validation significance:

- all observation ranges are constrained
- risk mode is controlled with `Literal`
- channels for alert subscription are restricted to `webhook`, `email`, `sms`, `log`
- batch jobs allow up to 40 locations
- multi-location comparison allows up to 10 locations
## 11. Database Design

Database logic is in [storage.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py).

Database engine: SQLite

Database file path: `expert_system/backend/weather_expert.db`

Connection helper: `_connect()` at [storage.py:12](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L12)

### Tables currently created at startup

#### 11.1 `forecast_history`

Created at [storage.py:23](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L23)

Stores:

- timestamp
- location
- risk mode
- predicted condition
- rain probability
- alert level

Used by:

- `/api/v1/infer`
- history reading
- history analytics

#### 11.2 `audit_log`

Created at [storage.py:36](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L36)

Stores:

- timestamp
- actor
- action
- detail

Used to track:

- inference calls
- outcome reporting
- live weather calls
- subscription changes
- knowledge-base version operations
- batch job creation

#### 11.3 `forecast_outcomes`

Created at [storage.py:47](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L47)

Stores post-forecast ground truth for verification and calibration.

Fields include:

- predicted rain probability
- actual condition
- actual rainfall
- binary rain outcome
- absolute error
- Brier score

This is used by:

- `POST /api/v1/outcome`
- `GET /api/v1/calibration`

#### 11.4 `alert_subscriptions`

Created at [storage.py:64](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L64)

Stores user-defined alert rules.

Fields include:

- channel
- target
- location filter
- risk mode filter
- minimum rain probability
- minimum alert level
- enabled flag

#### 11.5 `notification_log`

Created at [storage.py:80](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L80)

Stores notification delivery records, including payload JSON.

#### 11.6 `knowledge_base_versions`

Created at [storage.py:92](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L92)

Stores snapshot versions of the knowledge base.

Fields include:

- version name
- created time
- created by
- notes
- full JSON payload
- active flag

#### 11.7 `live_weather_cache`

Created at [storage.py:105](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L105)

Stores cached live weather payloads keyed by provider and rounded coordinates.

### Database helper functions and what they do

- `write_forecast()` at [storage.py:118](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L118)
- `write_audit()` at [storage.py:141](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L141)
- `read_history()` at [storage.py:153](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L153)
- `read_history_analytics()` at [storage.py:200](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L200)
- `write_outcome()` at [storage.py:282](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L282)
- `read_calibration()` at [storage.py:318](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L318)
- `create_alert_subscription()` at [storage.py:381](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L381)
- `read_alert_subscriptions()` at [storage.py:416](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L416)
- `set_alert_subscription_enabled()` at [storage.py:433](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L433)
- `write_notification_log()` at [storage.py:445](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L445)
- `read_notification_log()` at [storage.py:471](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L471)
- `create_kb_version()` at [storage.py:493](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L493)
- `list_kb_versions()` at [storage.py:525](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L525)
- `activate_kb_version()` at [storage.py:540](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L540)
- `get_active_kb_version()` at [storage.py:554](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L554)
- `read_kb_version()` at [storage.py:575](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L575)
- `read_live_cache()` at [storage.py:595](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L595)
- `write_live_cache()` at [storage.py:613](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L613)

### Best DB explanation for viva

The project uses SQLite not only for forecast history and audit logs now, but also for outcome verification, calibration metrics, alert subscriptions, notification history, knowledge-base version snapshots, and live weather caching. The database supports the operational side of the expert system, while the actual reasoning still happens in Python code.

## 12. Knowledge Base and Runtime Knowledge

There are now 2 knowledge concepts.

### 12.1 Static default knowledge base

Defined in [knowledge_base.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\knowledge_base.py).

It contains:

- `BASE_PRIORS`
- `SEASONAL_MULTIPLIERS`
- `TERRAIN_MULTIPLIERS`
- `CLIMATE_ZONE_MULTIPLIERS`
- `MONTHLY_MULTIPLIERS`
- `RISK_MODE_ALERT_WEIGHTS`
- `RISK_MODE_THRESHOLDS`
- `expert_rules()`
- `infer_climate_zone()`
- `export_knowledge_base()`

`export_knowledge_base()` at [knowledge_base.py:97](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\knowledge_base.py#L97) serializes the static knowledge into a JSON-friendly dictionary.

### 12.2 Runtime knowledge resolution

Implemented in [runtime_knowledge.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\runtime_knowledge.py#L20).

Flow:

1. load default payload from `export_knowledge_base()`
2. check if there is an active version in the DB
3. validate that active payload contains all required keys
4. return active payload if valid
5. otherwise fall back to default knowledge

Required keys are enforced at [runtime_knowledge.py:9](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\runtime_knowledge.py#L9).

Important viva point:

This means the model logic can be changed at runtime without editing code, as long as a knowledge-base snapshot exists in the database.

## 13. Knowledge Base Versioning Endpoints

Implemented in [main.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py).

### `GET /api/v1/knowledge-base`

At [main.py:97](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L97)

Returns:

- active version name
- resolved runtime knowledge payload

### `GET /api/v1/knowledge-base/active`

At [main.py:360](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L360)

Returns either:

- default knowledge if no active DB version exists
- active version payload if a version is activated

### `GET /api/v1/knowledge-base/versions`

At [main.py:368](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L368)

Lists all stored KB snapshots.

### `POST /api/v1/knowledge-base/versions`

At [main.py:374](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L374)

Behavior:

- admin only
- snapshots current runtime knowledge
- stores it as a new row
- can optionally mark it active

### `POST /api/v1/knowledge-base/versions/{version_id}/activate`

At [main.py:392](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L392)

Behavior:

- admin only
- deactivates all versions
- activates one selected version

## 14. Static Expert Knowledge

Inside [knowledge_base.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\knowledge_base.py):

- priors define default starting belief for each condition
- seasonal multipliers model weather seasonality
- terrain multipliers model terrain-sensitive effects
- climate-zone multipliers model location macro-patterns
- monthly multipliers add month-specific refinements
- alert weights and thresholds map forecast probabilities to domain-specific risk interpretation

Expert rules in `expert_rules()` start at [knowledge_base.py:113](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\knowledge_base.py#L113).

Rules include support for:

- rain
- drizzle
- thunderstorm
- fog
- clear
- windy

Important detail:

Rules return `RuleEffect` objects. They do not directly force final output. They only add evidence to one competing weather state.
## 15. Data Intelligence Layer

Implemented in [data_intelligence.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\data_intelligence.py).

### `data_quality(obs)`

Location: [data_intelligence.py:19](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\data_intelligence.py#L19)

Responsibilities:

- average source confidence values
- clamp sensor reliability into a safe range
- impute missing fields like `uv_index`, `visibility_km`, and `recent_rain_mm`
- compute uncertainty penalty

Returned values:

- `sensor_reliability`
- `imputed_fields`
- `uncertainty_penalty`

### `apply_historical_baseline(obs, climate_zone, month)`

Location: [data_intelligence.py:42](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\data_intelligence.py#L42)

Creates bias features by comparing observation values to broad climate-zone baselines.

Returned bias terms:

- humidity bias
- pressure bias
- wind bias
- cloud bias
- seasonal bias

In the current engine, humidity bias and seasonal bias are the most directly used ones.

## 16. Synthetic Climatology Dataset

Implemented in [climatology_dataset.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py).

This is one of the biggest new additions.

### What it is

It is a synthetic multi-decade climatology generator, not a real imported dataset file.

It programmatically builds `DATASET_ROWS` at import time in [climatology_dataset.py:134](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L134).

### How it is constructed

City profiles are defined in `CITY_CLIMATE_PROFILE` at [climatology_dataset.py:8](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L8).

Then:

1. years 2006 to 2025 are enumerated
2. every month is processed
3. 28 synthetic days per month are generated
4. condition distributions are synthesized using seasonal signals and random noise
5. aggregated monthly rows are stored per city and year

### Important helper functions

- `_seasonal_rain_signal()` at [climatology_dataset.py:42](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L42)
- `_winter_fog_signal()` at [climatology_dataset.py:48](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L48)
- `_summer_clear_signal()` at [climatology_dataset.py:52](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L52)
- `_condition_distribution()` at [climatology_dataset.py:56](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L56)
- `_city_features()` at [climatology_dataset.py:82](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L82)
- `build_dataset()` at [climatology_dataset.py:97](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L97)
- `dataset_stats()` at [climatology_dataset.py:137](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L137)
- `climatology_distribution()` at [climatology_dataset.py:161](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L161)

### Why it is used

It is used only for low-weight prior smoothing, not for training.

That exact design intent is stated in `dataset_stats()` notes at [climatology_dataset.py:146](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py#L146).

Best viva answer:

The climatology dataset is synthetic and is used to slightly stabilize probabilities using long-run city-month patterns. It does not replace the expert engine and does not directly fit the model.

## 17. Core Inference Engine

Implemented in [probabilistic_engine.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py).

Main function: `infer_weather()` at [probabilistic_engine.py:316](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L316)

This is the heart of the system.

### Important update in the pulled version

The engine is now knowledge-base aware and runtime configurable.

`infer_weather()` accepts:

- observation
- location
- horizon
- risk mode
- custom thresholds
- `knowledge_base`
- `include_horizons`

That means the inference engine no longer depends only on static constants. It can use dynamic knowledge snapshots loaded from SQLite.

## 18. Step-by-Step Execution Flow for `/api/v1/infer`

This is the most important viva section.

### Step 1. Request reaches route

Route: [main.py:111](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L111)

FastAPI validates the request with `InferenceRequest`.

### Step 2. Authorization runs

`Depends(authorize)` checks the API key and requested role.

### Step 3. Observation model becomes dict

At [main.py:113](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L113):

`obs = request.observation.model_dump()`

### Step 4. Runtime knowledge is resolved

At [main.py:114](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L114):

`runtime_knowledge = resolve_runtime_knowledge()`

This may come from DB snapshot or default static knowledge.

### Step 5. Core inference runs

At [main.py:115](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L115), `infer_weather()` is called.

### Step 6. Engine loads runtime knowledge sections

At [probabilistic_engine.py:326](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L326), the engine extracts:

- base priors
- seasonal multipliers
- terrain multipliers
- climate-zone multipliers
- monthly multipliers
- risk mode alert weights
- risk mode thresholds

### Step 7. Data quality analysis

At [probabilistic_engine.py:337](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L337), `data_quality(obs)` runs.

### Step 8. Climate baseline biasing

At [probabilistic_engine.py:338](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L338), `apply_historical_baseline()` runs.

### Step 9. Log-prior scores are initialized

At [probabilistic_engine.py:340](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L340), each condition starts from `log(base_prior)`.

### Step 10. Feature contributions are computed

At [probabilistic_engine.py:341](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L341), `_feature_contributions()` computes engineered scores for every condition.

### Step 11. Contextual knowledge multipliers are applied

At [probabilistic_engine.py:342](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L342), `_apply_knowledge_multipliers()` combines feature contribution with:

- season
- terrain
- climate zone
- month

### Step 12. Expert rules are applied

At [probabilistic_engine.py:352](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L352), `_apply_rules()` adds `log(weight)` deltas from expert rules.

### Step 13. Horizon-based score adjustments are added

At [probabilistic_engine.py:354](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L354), rain and thunderstorm are slightly boosted for longer forecast horizons.

### Step 14. Softmax normalization

At [probabilistic_engine.py:358](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L358), scores are converted into a probability distribution.

### Step 15. Dynamic transition post-processing

At [probabilistic_engine.py:359](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L359), `_dynamic_transition()` shifts probabilities toward rain-related states for longer horizons.

### Step 16. Reliability calibration

At [probabilistic_engine.py:360](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L360), `_calibrate()` sharpens or softens the distribution using sensor reliability.

### Step 17. Climatology smoothing

At [probabilistic_engine.py:361](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L361), `_climatology_smoothing()` blends the current probability distribution with the synthetic climatology distribution for that location and month.

This is the key new step added in the updated project.

How smoothing works:

- city-month climatology distribution is fetched
- sample count is read
- blend alpha is computed at [probabilistic_engine.py:304](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L304)
- final probability = `(1 - alpha) * current_prob + alpha * climatology_prob`

Alpha is clamped between `0.05` and `0.16`, so climatology is always low-weight.

### Step 18. Rain probability is derived

At [probabilistic_engine.py:363](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L363)

Composite formula:

- rain
- plus weighted drizzle
- plus weighted thunderstorm

### Step 19. Confidence is computed

At [probabilistic_engine.py:365](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L365), confidence is based on entropy minus uncertainty penalty.

### Step 20. Expected rainfall is simulated

At [probabilistic_engine.py:366](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L366), `_expected_rainfall_mm()` runs a Monte Carlo-like rainfall estimate using gamma sampling.

### Step 21. Top class becomes predicted condition

At [probabilistic_engine.py:367](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L367), the max probability class is chosen.

### Step 22. Secondary forecast artifacts are generated

The engine generates:

- key factors
- feature attributions
- scenarios
- event probabilities
- intensity bands
- counterfactuals
- explanation
- climatology metadata
- per-horizon forecasts

### Step 23. Multi-horizon recursion happens

At [probabilistic_engine.py:375](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L375), `_horizon_projection()` may recursively call `infer_weather()` with `include_horizons=False`.

Important viva point:

This is controlled recursion and does not recurse infinitely.

### Step 24. Response model is built

Back in [main.py:129](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L129), `InferenceResponse` is constructed.

### Step 25. Forecast summary is persisted

At [main.py:153](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L153), `write_forecast()` stores summary forecast data.

### Step 26. Alert subscriptions are checked

At [main.py:165](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L165), `_trigger_subscriptions()` checks all enabled subscriptions.

### Step 27. Audit log is written

At [main.py:176](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L176), audit data includes how many alerts were triggered.

### Step 28. Response is returned to frontend

The frontend renders the results.
## 19. Important Functions in the Inference Engine

- `_softmax()` at [probabilistic_engine.py:30](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L30)
- `_feature_contributions()` at [probabilistic_engine.py:37](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L37)
- `_apply_knowledge_multipliers()` at [probabilistic_engine.py:99](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L99)
- `_apply_rules()` at [probabilistic_engine.py:123](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L123)
- `_dynamic_transition()` at [probabilistic_engine.py:132](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L132)
- `_calibrate()` at [probabilistic_engine.py:143](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L143)
- `_confidence()` at [probabilistic_engine.py:153](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L153)
- `_expected_rainfall_mm()` at [probabilistic_engine.py:160](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L160)
- `_alert_level()` at [probabilistic_engine.py:174](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L174)
- `_recommendations()` at [probabilistic_engine.py:196](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L196)
- `_scenario_simulation()` at [probabilistic_engine.py:220](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L220)
- `_event_probabilities()` at [probabilistic_engine.py:230](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L230)
- `_intensity_bands()` at [probabilistic_engine.py:241](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L241)
- `_counterfactuals()` at [probabilistic_engine.py:255](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L255)
- `_feature_attributions()` at [probabilistic_engine.py:263](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L263)
- `_horizon_projection()` at [probabilistic_engine.py:271](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L271)
- `_climatology_smoothing()` at [probabilistic_engine.py:301](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L301)
- `infer_weather()` at [probabilistic_engine.py:316](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py#L316)

## 20. Alerting Subsystem

Implemented in [alerts.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\alerts.py).

### Trigger decision

`should_trigger()` at [alerts.py:24](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\alerts.py#L24)

A subscription triggers only if all conditions match:

- subscription is enabled
- location matches or is wildcard `*`
- risk mode matches or is wildcard `*`
- forecast rain probability exceeds threshold
- forecast alert level rank meets or exceeds subscription minimum level

Alert level ranking is defined at [alerts.py:12](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\alerts.py#L12).

### Delivery

`deliver_notification()` at [alerts.py:55](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\alerts.py#L55)

Channels:

- `webhook`: actual HTTP POST attempted
- `email`: simulated queue message
- `sms`: simulated queue message
- `log`: log-only delivery

Webhook delivery helper is `_deliver_webhook()` at [alerts.py:38](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\alerts.py#L38).

Every delivery attempt is persisted through `write_notification_log()`.

### Subscription orchestration inside inference

`_trigger_subscriptions()` is defined in [main.py:71](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L71).

It is called after every `/infer` request, not after multi-location or batch routes.

## 21. Outcome Reporting and Calibration

### Outcome reporting route

`POST /api/v1/outcome` at [main.py:223](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L223)

Behavior:

1. accept actual observed outcome
2. derive binary rain outcome
3. compute absolute error
4. compute Brier score
5. store record in `forecast_outcomes`
6. return updated calibration snapshot

Binary rain rule used by the route at [main.py:226](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L226):

Observed rain is considered true if:

- actual condition is `rain`, `drizzle`, or `thunderstorm`
- or actual rainfall is at least `0.5 mm`

### Calibration endpoint

`GET /api/v1/calibration` at [main.py:249](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L249)

Internally it calls `read_calibration()` at [storage.py:318](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L318).

Returned calibration summary includes:

- overall sample count
- average Brier score
- average absolute error
- reliability bins by predicted probability range
- per-location calibration summary

Best viva answer:

This lets the system evaluate how well predicted rain probability aligns with actual outcomes. That is why it is not only predictive but also self-evaluating.

## 22. History and Analytics

### Filtered history route

`GET /api/v1/history` at [main.py:186](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L186)

Supported filters:

- `limit`
- `location`
- `risk_mode`
- `alert_level`
- `date_from`
- `date_to`

These are passed into `read_history()`.

### Analytics route

`GET /api/v1/history/analytics` at [main.py:207](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L207)

Internally it calls `read_history_analytics()` at [storage.py:200](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py#L200).

Analytics output includes:

- summary totals
- average rain probability
- ratio of high/severe alerts
- daily timeline rollups
- per-location aggregates

## 23. Live Weather Provider System

Implemented in [weather_provider.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py).

This module is now much richer than before.

### Provider options

- Open-Meteo via `_open_meteo()` at [weather_provider.py:22](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py#L22)
- wttr.in via `_wttr()` at [weather_provider.py:40](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py#L40)
- synthetic fallback via `_synthetic()` at [weather_provider.py:57](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py#L57)

### Main fetch function

`fetch_live_weather()` at [weather_provider.py:68](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py#L68)

Behavior:

1. choose provider order based on `provider_preference`
2. check persistent SQLite cache first
3. if cache hit, return cached payload and mark source as `cache`
4. otherwise call provider over network
5. store successful live payload into cache with expiry
6. if all providers fail, return deterministic synthetic fallback

### Cache behavior

Cache key comes from provider + rounded lat/lon using `_cache_key()` at [weather_provider.py:18](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py#L18).

Cache data is stored in `live_weather_cache` table.

Important viva point:

The live weather layer now supports multiple providers, persistent cache, provider preference, and graceful degradation.

## 24. Multi-Location Inference

Route: `POST /api/v1/infer/multi-location` at [main.py:303](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py#L303)

Execution:

1. resolve runtime knowledge once
2. loop over requested locations
3. run `infer_weather()` separately for each location
4. collect simplified summary per location
5. return count and items
6. write audit log

Important detail:

The same observation is reused, but location changes climate zone and climatology smoothing context, so output can differ city to city.

## 25. Batch Forecast Jobs

Implemented in [batch_jobs.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\batch_jobs.py).

### Why it exists

This supports larger multi-location workloads asynchronously without blocking the caller until all results are finished.

### How it works

`create_batch_job()` at [batch_jobs.py:20](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\batch_jobs.py#L20):

- creates a UUID job id
- creates in-memory job record
- stores it in `_JOB_STORE`
- starts a daemon thread

`_run_job()` at [batch_jobs.py:63](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\batch_jobs.py#L63):

- marks job as running
- resolves runtime knowledge once
- loops through all locations
- calls `infer_weather()` for each location
- appends simplified item
- updates progress counters
- marks status completed or failed

### Important implementation detail

Batch jobs are not persisted in SQLite. They are stored only in process memory in `_JOB_STORE`.

So if the server restarts, running/completed jobs are lost.

That is an important limitation to mention honestly.
## 26. Frontend Summary

Frontend files:

- [index.html](c:\Users\yuvra\Desktop\PROJECTS\expert_system\frontend\index.html)
- [app.js](c:\Users\yuvra\Desktop\PROJECTS\expert_system\frontend\app.js)
- [styles.css](c:\Users\yuvra\Desktop\PROJECTS\expert_system\frontend\styles.css)

The frontend is still a single-page plain JavaScript dashboard.

Main responsibilities:

- collect city, risk mode, horizon, and weather inputs
- build payload for `/api/v1/infer`
- build payload for `/api/v1/infer/multi-location`
- render forecast panels and heatmaps
- render India map interactions

Important note for viva:

The backend has advanced new capabilities like calibration, subscriptions, KB versioning, and batch jobs, but the frontend is mainly focused on forecast and heatmap visualization. Some newer backend features are API-first and may not yet have full UI panels.

## 27. Exact "Where is What" Map

If someone asks where something is implemented:

- API routes: [main.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\main.py)
- auth: [security.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\security.py)
- DB schema and persistence: [storage.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\storage.py)
- static knowledge base: [knowledge_base.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\knowledge_base.py)
- runtime KB selection: [runtime_knowledge.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\runtime_knowledge.py)
- climatology generation and stats: [climatology_dataset.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\climatology_dataset.py)
- data quality and baseline: [data_intelligence.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\data_intelligence.py)
- main inference engine: [probabilistic_engine.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\probabilistic_engine.py)
- live provider and caching: [weather_provider.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\weather_provider.py)
- alert triggering and delivery: [alerts.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\alerts.py)
- async batch jobs: [batch_jobs.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\batch_jobs.py)
- API schemas: [schemas.py](c:\Users\yuvra\Desktop\PROJECTS\expert_system\backend\app\schemas.py)

## 28. Strengths of the Updated Project

1. It is now more complete than a basic expert system demo.
2. It supports explanation, persistence, evaluation, and operational alerting.
3. It has runtime knowledge-base versioning.
4. It includes a climatology smoothing layer.
5. It supports history analytics and forecast verification.
6. It has live provider abstraction with cache.
7. It supports alert subscriptions and notification logs.
8. It supports async batch forecast jobs.

## 29. Honest Limitations

1. Climatology dataset is synthetic, not real observed meteorological history.
2. Batch jobs are in-memory only and vanish on restart.
3. SQLite is good for demo and local deployment, not ideal for heavy concurrent production use.
4. Frontend does not expose all backend enterprise features yet.
5. Expert rules and multipliers are still hand-crafted.
6. Expected rainfall is stochastic and can vary slightly across runs.
7. Live provider dependence can fail, though cache and fallback reduce the impact.

## 30. Best Viva Answers for New Features

### Q. What changed in the updated version?

The updated version adds runtime knowledge-base snapshots and activation, climatology-based probability smoothing, live weather provider abstraction with persistent caching, alert subscriptions and notification logging, forecast outcome reporting with Brier score based calibration, filtered history analytics, and in-memory threaded batch forecast jobs.

### Q. How is the knowledge base dynamic now?

The system can store whole knowledge-base payloads in the `knowledge_base_versions` table. `resolve_runtime_knowledge()` loads the active one if valid, so inference can run with a DB-backed knowledge version instead of only hard-coded constants.

### Q. How is calibration measured?

After a forecast, an actual observed outcome can be submitted to `/api/v1/outcome`. The backend converts it into a binary rain outcome and computes absolute error and Brier score. These are stored in `forecast_outcomes`, and `/api/v1/calibration` summarizes reliability bins and average scores.

### Q. What is the purpose of the synthetic climatology dataset?

It is a low-weight prior smoother. It slightly stabilizes probabilities using long-run city and month patterns so the forecast distribution is less noisy. It does not train the model and does not replace the expert rules.

### Q. How do subscriptions work?

Subscriptions are stored in SQLite with conditions like location, risk mode, minimum rain probability, and minimum alert level. After `/infer`, the backend checks all enabled subscriptions. Matching ones trigger notifications, and every delivery attempt is logged.

### Q. How does live weather caching work?

For a provider and rounded coordinates, the backend checks `live_weather_cache`. If a fresh cached entry exists, it returns that. Otherwise it calls the provider, stores the payload with an expiry, and returns live data. If all providers fail, it returns synthetic fallback weather.

### Q. Are batch jobs truly asynchronous?

They are asynchronous relative to the request because they run in a background thread, but they are not distributed jobs and not persisted in a queue system. They live only in the current server process.

## 31. Best 2-Minute Project Explanation

This project is a full-stack hybrid probabilistic weather expert system. The backend is built with FastAPI, and the frontend is a plain JavaScript dashboard. The system takes a structured weather observation and predicts weather condition probabilities, rain probability, expected rainfall, alert level, scenarios, event timing, and recommendations. The reasoning pipeline starts from priors, adds engineered feature scores, applies contextual multipliers like season, terrain, climate zone, and month, then applies expert rules such as low pressure, high humidity, and fog conditions. The scores are converted into probabilities with softmax, adjusted by dynamic horizon logic, calibrated using sensor reliability, and now also smoothed using a low-weight synthetic climatology dataset. The project also stores forecast history in SQLite, supports analytics, records actual outcomes to compute Brier score calibration, supports alert subscriptions and notification logs, allows versioning and activation of the knowledge base at runtime, and provides in-memory background batch jobs for larger forecast requests.

## 32. Best 30-Second Database Explanation

The project uses SQLite as an operational database. It stores forecast history, audit logs, actual outcomes for calibration, alert subscriptions, notification logs, knowledge-base versions, and live weather cache entries. The database supports persistence, monitoring, calibration, and runtime configurability. The actual inference logic still runs in Python code.

## 33. Best 30-Second Execution Flow Explanation

The frontend sends an observation to the FastAPI `/infer` route. The backend validates the payload, checks API headers, resolves the active runtime knowledge base, and calls `infer_weather()`. The engine computes data quality, baseline bias, feature scores, knowledge multipliers, rule contributions, softmax probabilities, dynamic horizon transition, reliability calibration, climatology smoothing, confidence, rainfall, alert level, and explainability outputs. Then the route writes forecast history, checks subscriptions, logs audit details, and returns the structured response.

## 34. Final One-Line Summary

This project is a hybrid probabilistic weather expert system with a FastAPI backend, SQLite-backed operations layer, runtime knowledge-base versioning, climatology-aware smoothing, alerting and calibration support, and a plain JavaScript dashboard frontend.

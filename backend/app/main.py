from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .knowledge_base import (
    BASE_PRIORS,
    CLIMATE_ZONE_MULTIPLIERS,
    MONTHLY_MULTIPLIERS,
    RISK_MODE_THRESHOLDS,
    SEASONAL_MULTIPLIERS,
    TERRAIN_MULTIPLIERS,
)
from .probabilistic_engine import infer_weather
from .schemas import (
    ConditionProbability,
    InferenceRequest,
    InferenceResponse,
    MultiLocationItem,
    MultiLocationRequest,
    MultiLocationResponse,
)
from .security import authorize
from .storage import init_db, read_history, write_audit, write_forecast
from .weather_provider import fetch_live_weather


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Probabilistic weather expert system using hybrid Bayesian scoring + rule reasoning.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/knowledge-base")
def knowledge_base() -> dict[str, Any]:
    return {
        "base_priors": BASE_PRIORS,
        "seasonal_multipliers": SEASONAL_MULTIPLIERS,
        "terrain_multipliers": TERRAIN_MULTIPLIERS,
        "climate_zone_multipliers": CLIMATE_ZONE_MULTIPLIERS,
        "monthly_multipliers": MONTHLY_MULTIPLIERS,
        "risk_mode_thresholds": RISK_MODE_THRESHOLDS,
    }


@app.post("/api/v1/infer", response_model=InferenceResponse)
def infer(request: InferenceRequest, role: str = Depends(authorize)) -> InferenceResponse:
    obs = request.observation.model_dump()
    result = infer_weather(
        obs,
        location=request.location,
        horizon_hours=request.horizon_hours,
        risk_mode=request.risk_mode,
        custom_thresholds=request.custom_thresholds,
    )

    condition_probabilities = [
        ConditionProbability(condition=condition, probability=round(prob, 4))
        for condition, prob in sorted(result["condition_probabilities"].items(), key=lambda item: item[1], reverse=True)
    ]

    response = InferenceResponse(
        location=request.location,
        risk_mode=request.risk_mode,
        horizon_hours=request.horizon_hours,
        predicted_condition=result["predicted_condition"],
        condition_probabilities=condition_probabilities,
        rain_probability=result["rain_probability"],
        expected_rainfall_mm=result["expected_rainfall_mm"],
        confidence_score=result["confidence_score"],
        alert_level=result["alert_level"],
        expert_recommendations=result["expert_recommendations"],
        key_factors=result["key_factors"],
        feature_attributions=result["feature_attributions"],
        rule_trace=result["rule_trace"],
        counterfactuals=result["counterfactuals"],
        scenarios=result["scenarios"],
        horizons=result["horizons"],
        event_probabilities=result["event_probabilities"],
        intensity_bands=result["intensity_bands"],
        data_quality=result["data_quality"],
        explanation=result["explanation"],
    )

    now = datetime.now(timezone.utc).isoformat()
    write_forecast(
        {
            "timestamp_utc": now,
            "location": request.location,
            "risk_mode": request.risk_mode,
            "predicted_condition": response.predicted_condition,
            "rain_probability": response.rain_probability,
            "alert_level": response.alert_level,
        }
    )
    write_audit(now, role, "infer", f"location={request.location}; risk_mode={request.risk_mode}")

    return response


@app.get("/api/v1/history")
def history(limit: int = 50, _: str = Depends(authorize)) -> dict[str, Any]:
    items = read_history(limit=max(1, min(limit, 200)))
    return {"count": len(items), "items": items}


@app.get("/api/v1/live-weather")
def live_weather(lat: float, lon: float, role: str = Depends(authorize)) -> dict[str, Any]:
    payload = fetch_live_weather(lat=lat, lon=lon)
    write_audit(datetime.now(timezone.utc).isoformat(), role, "live_weather", f"lat={lat};lon={lon};source={payload['source']}")
    return payload


@app.post("/api/v1/infer/multi-location", response_model=MultiLocationResponse)
def infer_multi_location(request: MultiLocationRequest, role: str = Depends(authorize)) -> MultiLocationResponse:
    items: list[MultiLocationItem] = []
    for location in request.locations:
        result = infer_weather(
            request.observation.model_dump(),
            location=location,
            horizon_hours=request.horizon_hours,
            risk_mode=request.risk_mode,
            custom_thresholds={},
        )
        items.append(
            MultiLocationItem(
                location=location,
                predicted_condition=result["predicted_condition"],
                rain_probability=result["rain_probability"],
                alert_level=result["alert_level"],
            )
        )
    write_audit(
        datetime.now(timezone.utc).isoformat(),
        role,
        "infer_multi_location",
        f"locations={len(request.locations)}; risk_mode={request.risk_mode}",
    )
    return MultiLocationResponse(count=len(items), items=items)

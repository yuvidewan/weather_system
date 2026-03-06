from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .knowledge_base import BASE_PRIORS, SEASONAL_MULTIPLIERS, TERRAIN_MULTIPLIERS
from .probabilistic_engine import infer_weather
from .schemas import ConditionProbability, InferenceRequest, InferenceResponse


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

INFERENCE_HISTORY: list[dict[str, Any]] = []


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
    }


@app.post("/api/v1/infer", response_model=InferenceResponse)
def infer(request: InferenceRequest) -> InferenceResponse:
    result = infer_weather(request.observation.model_dump(), request.horizon_hours)

    condition_probabilities = [
        ConditionProbability(condition=condition, probability=round(prob, 4))
        for condition, prob in sorted(result["condition_probabilities"].items(), key=lambda item: item[1], reverse=True)
    ]

    response = InferenceResponse(
        location=request.location,
        horizon_hours=request.horizon_hours,
        predicted_condition=result["predicted_condition"],
        condition_probabilities=condition_probabilities,
        rain_probability=result["rain_probability"],
        expected_rainfall_mm=result["expected_rainfall_mm"],
        confidence_score=result["confidence_score"],
        alert_level=result["alert_level"],
        expert_recommendations=result["expert_recommendations"],
        key_factors=result["key_factors"],
        explanation=result["explanation"],
    )

    INFERENCE_HISTORY.append(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "location": request.location,
            "predicted_condition": response.predicted_condition,
            "rain_probability": response.rain_probability,
            "alert_level": response.alert_level,
        }
    )
    if len(INFERENCE_HISTORY) > 50:
        del INFERENCE_HISTORY[0]

    return response


@app.get("/api/v1/history")
def history() -> dict[str, Any]:
    return {"count": len(INFERENCE_HISTORY), "items": INFERENCE_HISTORY}


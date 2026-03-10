from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .alerts import deliver_notification, should_trigger
from .batch_jobs import create_batch_job, get_batch_job, list_batch_jobs
from .climatology_dataset import dataset_stats
from .config import settings
from .knowledge_base import export_knowledge_base
from .probabilistic_engine import infer_weather
from .runtime_knowledge import resolve_runtime_knowledge
from .schemas import (
    AlertSubscriptionRequest,
    BatchJobRequest,
    ConditionProbability,
    InferenceRequest,
    InferenceResponse,
    KnowledgeBaseVersionCreateRequest,
    MultiLocationItem,
    MultiLocationRequest,
    MultiLocationResponse,
    OutcomeReportRequest,
)
from .security import authorize
from .storage import (
    activate_kb_version,
    create_alert_subscription,
    create_kb_version,
    get_active_kb_version,
    init_db,
    list_kb_versions,
    read_alert_subscriptions,
    read_calibration,
    read_history,
    read_history_analytics,
    read_kb_version,
    read_notification_log,
    set_alert_subscription_enabled,
    write_audit,
    write_forecast,
    write_outcome,
)
from .weather_provider import fetch_live_weather


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
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


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trigger_subscriptions(forecast: dict[str, Any]) -> int:
    triggered = 0
    subscriptions = read_alert_subscriptions(enabled_only=True)
    for subscription in subscriptions:
        if should_trigger(subscription, forecast):
            deliver_notification(subscription, forecast)
            triggered += 1
    return triggered


def _coerce_iso_or_none(value: str | None) -> str | None:
    if not value:
        return None
    return value


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "timestamp_utc": _now_utc(),
    }


@app.get("/api/v1/knowledge-base")
def knowledge_base() -> dict[str, Any]:
    active = get_active_kb_version()
    return {
        "active_version": active["version_name"] if active else "default",
        "knowledge": resolve_runtime_knowledge(),
    }


@app.get("/api/v1/dataset/stats")
def dataset_metadata(_: str = Depends(authorize)) -> dict[str, Any]:
    return dataset_stats()


@app.post("/api/v1/infer", response_model=InferenceResponse)
def infer(request: InferenceRequest, role: str = Depends(authorize)) -> InferenceResponse:
    obs = request.observation.model_dump()
    runtime_knowledge = resolve_runtime_knowledge()
    result = infer_weather(
        obs,
        location=request.location,
        horizon_hours=request.horizon_hours,
        risk_mode=request.risk_mode,
        custom_thresholds=request.custom_thresholds,
        knowledge_base=runtime_knowledge,
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
        climatology_meta=result["climatology_meta"],
        explanation=result["explanation"],
    )

    now = _now_utc()
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

    trigger_count = _trigger_subscriptions(
        {
            "location": request.location,
            "risk_mode": request.risk_mode,
            "rain_probability": response.rain_probability,
            "alert_level": response.alert_level,
            "predicted_condition": response.predicted_condition,
            "horizon_hours": request.horizon_hours,
            "timestamp_utc": now,
        }
    )
    write_audit(
        now,
        role,
        "infer",
        f"location={request.location};risk_mode={request.risk_mode};alerts_triggered={trigger_count}",
    )

    return response


@app.get("/api/v1/history")
def history(
    limit: int = Query(50, ge=1, le=200),
    location: str | None = None,
    risk_mode: str | None = None,
    alert_level: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    _: str = Depends(authorize),
) -> dict[str, Any]:
    items = read_history(
        limit=limit,
        location=location,
        risk_mode=risk_mode,
        alert_level=alert_level,
        date_from=_coerce_iso_or_none(date_from),
        date_to=_coerce_iso_or_none(date_to),
    )
    return {"count": len(items), "items": items}


@app.get("/api/v1/history/analytics")
def history_analytics(
    location: str | None = None,
    risk_mode: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    _: str = Depends(authorize),
) -> dict[str, Any]:
    return read_history_analytics(
        location=location,
        risk_mode=risk_mode,
        date_from=_coerce_iso_or_none(date_from),
        date_to=_coerce_iso_or_none(date_to),
    )


@app.post("/api/v1/outcome")
def report_outcome(payload: OutcomeReportRequest, role: str = Depends(authorize)) -> dict[str, Any]:
    ts = payload.timestamp_utc or _now_utc()
    observed_rain = 1 if payload.actual_condition in {"rain", "drizzle", "thunderstorm"} or payload.actual_rain_mm >= 0.5 else 0
    absolute_error = abs(payload.predicted_rain_probability - observed_rain)
    brier = (payload.predicted_rain_probability - observed_rain) ** 2

    write_outcome(
        {
            "timestamp_utc": ts,
            "location": payload.location,
            "risk_mode": payload.risk_mode,
            "horizon_hours": payload.horizon_hours,
            "predicted_rain_probability": payload.predicted_rain_probability,
            "actual_condition": payload.actual_condition,
            "actual_rain_mm": payload.actual_rain_mm,
            "outcome_rain": observed_rain,
            "absolute_error": round(absolute_error, 4),
            "brier_score": round(brier, 4),
        }
    )
    snapshot = read_calibration(payload.location)
    write_audit(ts, role, "report_outcome", f"location={payload.location};brier={round(brier, 4)}")
    return {"status": "recorded", "location": payload.location, "brier_score": round(brier, 4), "calibration": snapshot}


@app.get("/api/v1/calibration")
def calibration(location: str | None = None, _: str = Depends(authorize)) -> dict[str, Any]:
    return read_calibration(location)


@app.post("/api/v1/alerts/subscriptions")
def create_subscription(payload: AlertSubscriptionRequest, role: str = Depends(authorize)) -> dict[str, Any]:
    created_utc = _now_utc()
    if payload.channel == "webhook" and not payload.target:
        raise HTTPException(status_code=400, detail="Webhook channel requires target URL")

    sub_id = create_alert_subscription(
        {
            "created_utc": created_utc,
            "name": payload.name,
            "channel": payload.channel,
            "target": payload.target,
            "location": payload.location,
            "risk_mode": payload.risk_mode,
            "min_rain_probability": payload.min_rain_probability,
            "min_alert_level": payload.min_alert_level,
            "enabled": payload.enabled,
        }
    )
    write_audit(created_utc, role, "create_subscription", f"id={sub_id};name={payload.name}")
    return {"id": sub_id, "status": "created"}


@app.get("/api/v1/alerts/subscriptions")
def list_subscriptions(all: bool = False, _: str = Depends(authorize)) -> dict[str, Any]:
    items = read_alert_subscriptions(enabled_only=not all)
    return {"count": len(items), "items": items}


@app.post("/api/v1/alerts/subscriptions/{subscription_id}/toggle")
def toggle_subscription(subscription_id: int, enabled: bool, role: str = Depends(authorize)) -> dict[str, Any]:
    set_alert_subscription_enabled(subscription_id, enabled)
    write_audit(_now_utc(), role, "toggle_subscription", f"id={subscription_id};enabled={enabled}")
    return {"status": "updated", "id": subscription_id, "enabled": enabled}


@app.get("/api/v1/alerts/notifications")
def notifications(limit: int = Query(50, ge=1, le=300), _: str = Depends(authorize)) -> dict[str, Any]:
    items = read_notification_log(limit)
    return {"count": len(items), "items": items}


@app.get("/api/v1/live-weather")
def live_weather(lat: float, lon: float, provider: str = "auto", role: str = Depends(authorize)) -> dict[str, Any]:
    payload = fetch_live_weather(lat=lat, lon=lon, provider_preference=provider)
    write_audit(_now_utc(), role, "live_weather", f"lat={lat};lon={lon};provider={payload['provider']};source={payload['source']}")
    return payload


@app.post("/api/v1/infer/multi-location", response_model=MultiLocationResponse)
def infer_multi_location(request: MultiLocationRequest, role: str = Depends(authorize)) -> MultiLocationResponse:
    items: list[MultiLocationItem] = []
    runtime_knowledge = resolve_runtime_knowledge()
    for location in request.locations:
        result = infer_weather(
            request.observation.model_dump(),
            location=location,
            horizon_hours=request.horizon_hours,
            risk_mode=request.risk_mode,
            custom_thresholds={},
            knowledge_base=runtime_knowledge,
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
        _now_utc(),
        role,
        "infer_multi_location",
        f"locations={len(request.locations)};risk_mode={request.risk_mode}",
    )
    return MultiLocationResponse(count=len(items), items=items)


@app.post("/api/v1/jobs/forecast-batch")
def start_batch_job(payload: BatchJobRequest, role: str = Depends(authorize)) -> dict[str, Any]:
    job_id = create_batch_job(
        locations=payload.locations,
        observation=payload.observation.model_dump(),
        horizon_hours=payload.horizon_hours,
        risk_mode=payload.risk_mode,
        custom_thresholds=payload.custom_thresholds,
    )
    write_audit(_now_utc(), role, "batch_job_create", f"job_id={job_id};locations={len(payload.locations)}")
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/v1/jobs/forecast-batch/{job_id}")
def get_job(job_id: str, _: str = Depends(authorize)) -> dict[str, Any]:
    item = get_batch_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    return item


@app.get("/api/v1/jobs/forecast-batch")
def list_jobs(limit: int = Query(20, ge=1, le=100), _: str = Depends(authorize)) -> dict[str, Any]:
    items = list_batch_jobs(limit)
    return {"count": len(items), "items": items}


@app.get("/api/v1/knowledge-base/active")
def active_kb(_: str = Depends(authorize)) -> dict[str, Any]:
    active = get_active_kb_version()
    if not active:
        return {"source": "default", "payload": export_knowledge_base()}
    return {"source": "versioned", **active}


@app.get("/api/v1/knowledge-base/versions")
def kb_versions(_: str = Depends(authorize)) -> dict[str, Any]:
    items = list_kb_versions()
    return {"count": len(items), "items": items}


@app.post("/api/v1/knowledge-base/versions")
def create_kb_snapshot(payload: KnowledgeBaseVersionCreateRequest, role: str = Depends(authorize)) -> dict[str, Any]:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin role can create knowledge-base versions")
    now = _now_utc()
    snapshot = resolve_runtime_knowledge()
    version_id = create_kb_version(
        version_name=payload.version_name,
        created_utc=now,
        created_by=role,
        notes=payload.notes,
        payload=snapshot,
        is_active=payload.activate,
    )
    write_audit(now, role, "kb_version_create", f"id={version_id};activate={payload.activate}")
    return {"status": "created", "id": version_id}


@app.post("/api/v1/knowledge-base/versions/{version_id}/activate")
def activate_version(version_id: int, role: str = Depends(authorize)) -> dict[str, Any]:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin role can activate knowledge-base versions")
    ok = activate_kb_version(version_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Knowledge-base version not found")
    item = read_kb_version(version_id)
    write_audit(_now_utc(), role, "kb_version_activate", f"id={version_id}")
    return {"status": "activated", "version": item}

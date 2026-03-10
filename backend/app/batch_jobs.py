from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from .probabilistic_engine import infer_weather
from .runtime_knowledge import resolve_runtime_knowledge


_JOB_STORE: dict[str, dict[str, Any]] = {}
_JOB_LOCK = threading.Lock()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_batch_job(
    *,
    locations: list[str],
    observation: dict[str, Any],
    horizon_hours: int,
    risk_mode: str,
    custom_thresholds: dict[str, float],
) -> str:
    unique_locations = list(dict.fromkeys(locations))
    job_id = str(uuid.uuid4())
    record = {
        "job_id": job_id,
        "status": "queued",
        "created_utc": _now_utc(),
        "completed_utc": None,
        "total": len(unique_locations),
        "done": 0,
        "error": None,
        "items": [],
        "request": {
            "locations": unique_locations,
            "horizon_hours": horizon_hours,
            "risk_mode": risk_mode,
        },
    }
    with _JOB_LOCK:
        _JOB_STORE[job_id] = record

    thread = threading.Thread(
        target=_run_job,
        kwargs={
            "job_id": job_id,
            "locations": unique_locations,
            "observation": observation,
            "horizon_hours": horizon_hours,
            "risk_mode": risk_mode,
            "custom_thresholds": custom_thresholds,
        },
        daemon=True,
    )
    thread.start()
    return job_id


def _run_job(
    *,
    job_id: str,
    locations: list[str],
    observation: dict[str, Any],
    horizon_hours: int,
    risk_mode: str,
    custom_thresholds: dict[str, float],
) -> None:
    with _JOB_LOCK:
        _JOB_STORE[job_id]["status"] = "running"
    runtime_knowledge = resolve_runtime_knowledge()

    try:
        for location in locations:
            result = infer_weather(
                observation,
                location=location,
                horizon_hours=horizon_hours,
                risk_mode=risk_mode,
                custom_thresholds=custom_thresholds,
                knowledge_base=runtime_knowledge,
            )
            item = {
                "location": location,
                "predicted_condition": result["predicted_condition"],
                "rain_probability": result["rain_probability"],
                "alert_level": result["alert_level"],
                "confidence_score": result["confidence_score"],
            }
            with _JOB_LOCK:
                _JOB_STORE[job_id]["items"].append(item)
                _JOB_STORE[job_id]["done"] += 1

        with _JOB_LOCK:
            _JOB_STORE[job_id]["status"] = "completed"
            _JOB_STORE[job_id]["completed_utc"] = _now_utc()
    except Exception as exc:  # noqa: BLE001
        with _JOB_LOCK:
            _JOB_STORE[job_id]["status"] = "failed"
            _JOB_STORE[job_id]["error"] = str(exc)
            _JOB_STORE[job_id]["completed_utc"] = _now_utc()


def get_batch_job(job_id: str) -> dict[str, Any] | None:
    with _JOB_LOCK:
        item = _JOB_STORE.get(job_id)
        if not item:
            return None
        return {
            **item,
            "items": list(item["items"]),
            "request": dict(item["request"]),
        }


def list_batch_jobs(limit: int = 20) -> list[dict[str, Any]]:
    with _JOB_LOCK:
        values = list(_JOB_STORE.values())
    values.sort(key=lambda x: x["created_utc"], reverse=True)
    out = []
    for job in values[:limit]:
        out.append(
            {
                "job_id": job["job_id"],
                "status": job["status"],
                "created_utc": job["created_utc"],
                "completed_utc": job["completed_utc"],
                "total": job["total"],
                "done": job["done"],
                "error": job["error"],
            }
        )
    return out

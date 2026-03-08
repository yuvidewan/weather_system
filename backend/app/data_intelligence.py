from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


CLIMATE_BASELINES = {
    "humid_tropical": {"humidity_pct": 78, "pressure_hpa": 1006, "wind_kph": 17, "cloud_cover_pct": 68},
    "continental": {"humidity_pct": 58, "pressure_hpa": 1012, "wind_kph": 13, "cloud_cover_pct": 44},
    "arid": {"humidity_pct": 30, "pressure_hpa": 1008, "wind_kph": 15, "cloud_cover_pct": 20},
    "highland": {"humidity_pct": 64, "pressure_hpa": 1002, "wind_kph": 19, "cloud_cover_pct": 56},
    "plateau": {"humidity_pct": 54, "pressure_hpa": 1009, "wind_kph": 14, "cloud_cover_pct": 40},
}


def data_quality(obs: dict[str, Any]) -> dict[str, Any]:
    source_conf = obs.get("source_confidence", {})
    if not source_conf:
        source_conf = {"manual": 0.75}
    sensor_reliability = _clamp(sum(source_conf.values()) / len(source_conf), 0.25, 0.99)

    imputed_fields: list[str] = []
    if obs.get("uv_index") is None:
        obs["uv_index"] = 5.0
        imputed_fields.append("uv_index")
    if obs.get("visibility_km") is None:
        obs["visibility_km"] = 10.0
        imputed_fields.append("visibility_km")
    if obs.get("recent_rain_mm") is None:
        obs["recent_rain_mm"] = 0.0
        imputed_fields.append("recent_rain_mm")

    uncertainty_penalty = _clamp((1 - sensor_reliability) + 0.04 * len(imputed_fields), 0, 0.6)
    return {
        "sensor_reliability": round(sensor_reliability, 4),
        "imputed_fields": imputed_fields,
        "uncertainty_penalty": round(uncertainty_penalty, 4),
    }


def apply_historical_baseline(obs: dict[str, Any], climate_zone: str, month: int) -> dict[str, float]:
    baseline = CLIMATE_BASELINES.get(climate_zone, CLIMATE_BASELINES["continental"])
    month_offset = (month - 6.5) / 12.0
    return {
        "humidity_bias": round((obs["humidity_pct"] - baseline["humidity_pct"]) / 100, 4),
        "pressure_bias": round((obs["pressure_hpa"] - baseline["pressure_hpa"]) / 20, 4),
        "wind_bias": round((obs["wind_kph"] - baseline["wind_kph"]) / 30, 4),
        "cloud_bias": round((obs["cloud_cover_pct"] - baseline["cloud_cover_pct"]) / 100, 4),
        "seasonal_bias": round(month_offset, 4),
    }


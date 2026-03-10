from __future__ import annotations

import math
import random
from typing import Any

from .climatology_dataset import climatology_distribution
from .data_intelligence import apply_historical_baseline, data_quality
from .knowledge_base import (
    BASE_PRIORS as DEFAULT_BASE_PRIORS,
    CLIMATE_ZONE_MULTIPLIERS as DEFAULT_CLIMATE_ZONE_MULTIPLIERS,
    MONTHLY_MULTIPLIERS as DEFAULT_MONTHLY_MULTIPLIERS,
    RISK_MODE_ALERT_WEIGHTS as DEFAULT_RISK_MODE_ALERT_WEIGHTS,
    RISK_MODE_THRESHOLDS as DEFAULT_RISK_MODE_THRESHOLDS,
    SEASONAL_MULTIPLIERS as DEFAULT_SEASONAL_MULTIPLIERS,
    TERRAIN_MULTIPLIERS as DEFAULT_TERRAIN_MULTIPLIERS,
    expert_rules,
    infer_climate_zone,
)


CONDITIONS = list(DEFAULT_BASE_PRIORS.keys())
DEFAULT_HORIZONS = [1, 3, 6, 12, 24]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    peak = max(scores.values())
    exp_scores = {k: math.exp(v - peak) for k, v in scores.items()}
    total = sum(exp_scores.values())
    return {k: v / total for k, v in exp_scores.items()}


def _feature_contributions(obs: dict[str, Any], baseline: dict[str, float]) -> dict[str, float]:
    humidity = obs["humidity_pct"] / 100
    cloud = obs["cloud_cover_pct"] / 100
    pressure = obs["pressure_hpa"]
    wind = obs["wind_kph"]
    temp = obs["temperature_c"]
    dew_gap = temp - obs["dew_point_c"]
    recent_rain = obs["recent_rain_mm"]
    visibility = obs["visibility_km"]
    uv = obs["uv_index"]
    hour = obs["hour_24"]

    evening_convective = 1.0 if 15 <= hour <= 20 else 0.0
    night = 1.0 if hour <= 6 or hour >= 21 else 0.0

    return {
        "rain": (
            2.0 * humidity
            + 1.75 * cloud
            + 0.22 * recent_rain
            + (1008 - pressure) * 0.012
            + 0.35 * evening_convective
            + 0.4 * max(0, baseline["humidity_bias"])
            - 0.02 * max(0, uv - 8)
        ),
        "drizzle": (
            1.65 * humidity
            + 1.5 * cloud
            + 0.17 * recent_rain
            - 0.006 * abs(pressure - 1012)
            - 0.018 * max(0, wind - 30)
        ),
        "thunderstorm": (
            0.06 * max(0, temp - 24)
            + 1.22 * humidity
            + 1.0 * cloud
            + (1005 - pressure) * 0.02
            + 0.045 * wind
            + 0.5 * evening_convective
            + 0.22 * max(0, baseline["seasonal_bias"])
        ),
        "fog": (
            1.42 * humidity
            + 0.6 * cloud
            + 0.23 * night
            - 0.05 * wind
            + 0.12 * max(0, 4 - dew_gap)
            + 0.17 * max(0, 5 - visibility)
        ),
        "windy": 0.09 * wind + (1008 - pressure) * 0.011 + 0.12 * cloud - 0.02 * humidity + 0.08 * evening_convective,
        "clear": (
            1.7 * (1 - cloud)
            + 1.1 * (1 - humidity)
            + 0.04 * uv
            + 0.012 * max(0, pressure - 1012)
            - 0.05 * recent_rain
            - 0.35 * max(0, baseline["humidity_bias"])
        ),
        "cloudy": 1.82 * cloud + 0.82 * humidity + 0.01 * max(0, 1015 - pressure) - 0.02 * uv + 0.018 * max(0, 28 - temp),
    }


def _apply_knowledge_multipliers(
    scores: dict[str, float],
    obs: dict[str, Any],
    location: str,
    feature_contrib: dict[str, float],
    *,
    seasonal_multipliers: dict[str, dict[str, float]],
    terrain_multipliers: dict[str, dict[str, float]],
    climate_zone_multipliers: dict[str, dict[str, float]],
    monthly_multipliers: dict[int, dict[str, float]],
) -> tuple[dict[str, float], dict[str, float], str]:
    climate_zone = infer_climate_zone(location)
    impact_trace: dict[str, float] = {}
    for condition in CONDITIONS:
        season_mult = seasonal_multipliers.get(obs["season"], {}).get(condition, 1.0)
        terrain_mult = terrain_multipliers.get(obs["terrain"], {}).get(condition, 1.0)
        climate_mult = climate_zone_multipliers.get(climate_zone, {}).get(condition, 1.0)
        month_mult = monthly_multipliers.get(obs["month"], {}).get(condition, 1.0)
        blend = feature_contrib[condition] * season_mult * terrain_mult * climate_mult * month_mult
        scores[condition] += blend
        impact_trace[f"feature::{condition}"] = blend
    return scores, impact_trace, climate_zone


def _apply_rules(scores: dict[str, float], obs: dict[str, Any]) -> tuple[dict[str, float], list[dict[str, Any]]]:
    traces: list[dict[str, Any]] = []
    for effect in expert_rules(obs):
        delta = math.log(effect.weight)
        scores[effect.condition] += delta
        traces.append({"condition": effect.condition, "reason": effect.reason, "weight": effect.weight, "delta": delta})
    return scores, traces


def _dynamic_transition(probabilities: dict[str, float], horizon_hours: int) -> dict[str, float]:
    strength = _clamp((horizon_hours - 1) / 24, 0, 0.65)
    transitioned = dict(probabilities)
    rain_state = probabilities["rain"] + 0.4 * probabilities["drizzle"] + 0.55 * probabilities["thunderstorm"]
    transitioned["rain"] = _clamp((1 - strength) * probabilities["rain"] + strength * rain_state, 0.0001, 0.99)
    transitioned["drizzle"] = _clamp((1 - strength * 0.4) * probabilities["drizzle"], 0.0001, 0.99)
    transitioned["thunderstorm"] = _clamp((1 - strength * 0.2) * probabilities["thunderstorm"] + strength * 0.12 * rain_state, 0.0001, 0.99)
    total = sum(transitioned.values())
    return {k: v / total for k, v in transitioned.items()}


def _calibrate(probabilities: dict[str, float], reliability: float) -> dict[str, float]:
    calibrated = {}
    for condition, prob in probabilities.items():
        damp = 0.7 + 0.3 * reliability
        adjusted = (prob**damp) / ((prob**damp) + ((1 - prob) ** damp))
        calibrated[condition] = _clamp(adjusted, 0.0001, 0.999)
    total = sum(calibrated.values())
    return {k: v / total for k, v in calibrated.items()}


def _confidence(probabilities: dict[str, float], uncertainty_penalty: float) -> float:
    entropy = -sum(p * math.log(p + 1e-12) for p in probabilities.values())
    max_entropy = math.log(len(probabilities))
    certainty = 1 - entropy / max_entropy
    return _clamp(0.2 + 0.8 * certainty - uncertainty_penalty, 0.05, 0.99)


def _expected_rainfall_mm(obs: dict[str, Any], rain_prob: float, thunder_prob: float, horizon_hours: int) -> float:
    samples = []
    humidity = obs["humidity_pct"] / 100
    cloud = obs["cloud_cover_pct"] / 100
    trend_boost = 1.2 if obs["pressure_trend"] == "falling" else 1.0
    horizon_boost = _clamp(horizon_hours / 6, 0.6, 3.8)
    for _ in range(320):
        intensity = random.gammavariate(1.4 + 2.1 * thunder_prob, 2.4 + 1.5 * humidity)
        base = intensity * rain_prob * cloud * trend_boost * horizon_boost
        noise = random.uniform(-0.35, 0.7)
        samples.append(max(0.0, base + noise))
    return round(sum(samples) / len(samples), 2)


def _alert_level(
    rain_prob: float,
    thunder_prob: float,
    wind_prob: float,
    risk_mode: str,
    thresholds: dict[str, float],
    *,
    risk_mode_alert_weights: dict[str, dict[str, float]],
    risk_mode_thresholds: dict[str, dict[str, float]],
) -> str:
    weights = risk_mode_alert_weights.get(risk_mode, risk_mode_alert_weights["general"])
    score = weights["rain"] * rain_prob + weights["thunderstorm"] * thunder_prob + weights["windy"] * wind_prob
    config = {**risk_mode_thresholds.get(risk_mode, risk_mode_thresholds["general"]), **thresholds}
    if score >= config["severe"]:
        return "severe"
    if score >= config["high"]:
        return "high"
    if score >= config["moderate"]:
        return "moderate"
    return "low"


def _recommendations(risk_mode: str, rain_prob: float, thunder_prob: float, fog_prob: float, wind_prob: float) -> list[str]:
    base: list[str] = []
    if rain_prob >= 0.52:
        base.append("Carry rain protection and avoid flood-prone corridors.")
    if thunder_prob >= 0.35:
        base.append("Expect lightning risk; avoid exposed rooftops and open grounds.")
    if fog_prob >= 0.33:
        base.append("Use low-beam lights and reduce speed in low-visibility stretches.")
    if wind_prob >= 0.42:
        base.append("Secure loose structures and delay crane or rooftop operations.")

    mode_tips = {
        "agriculture": "Delay fertilizer/pesticide spray when rain chance is elevated.",
        "travel": "Add buffer time and prefer major roads if alert is high.",
        "events": "Prepare tent anchoring and covered backup areas.",
        "logistics": "Re-sequence loading windows for high-risk rainfall periods.",
    }
    if risk_mode in mode_tips:
        base.append(mode_tips[risk_mode])
    if not base:
        base.append("No major weather hazard likely in the selected horizon.")
    return base


def _scenario_simulation(rain_prob: float, expected_rainfall_mm: float) -> list[dict[str, float | str]]:
    best_prob = _clamp(rain_prob * 0.7, 0, 1)
    worst_prob = _clamp(rain_prob * 1.25, 0, 1)
    return [
        {"label": "best_case", "rain_probability": round(best_prob, 4), "expected_rainfall_mm": round(expected_rainfall_mm * 0.55, 2)},
        {"label": "expected_case", "rain_probability": round(rain_prob, 4), "expected_rainfall_mm": expected_rainfall_mm},
        {"label": "worst_case", "rain_probability": round(worst_prob, 4), "expected_rainfall_mm": round(expected_rainfall_mm * 1.6, 2)},
    ]


def _event_probabilities(probabilities: dict[str, float], rain_prob: float, horizon_hours: int) -> dict[str, float]:
    horizon_factor = _clamp(horizon_hours / 6, 0.3, 1.8)
    storm_prob = probabilities["thunderstorm"]
    heavy_prob = _clamp(0.55 * storm_prob + 0.45 * max(0, rain_prob - 0.35), 0, 1)
    return {
        "rain_onset_within_3h": round(_clamp(rain_prob * (0.8 / horizon_factor), 0, 1), 4),
        "storm_onset_within_6h": round(_clamp(storm_prob * (1.0 / max(horizon_factor, 0.6)), 0, 1), 4),
        "heavy_rain_within_12h": round(_clamp(heavy_prob * horizon_factor, 0, 1), 4),
    }


def _intensity_bands(rain_prob: float, thunder_prob: float) -> dict[str, float]:
    light = _clamp(0.5 * rain_prob + 0.15, 0, 1)
    moderate = _clamp(0.35 * rain_prob + 0.2 * thunder_prob, 0, 1)
    heavy = _clamp(0.22 * rain_prob + 0.45 * thunder_prob, 0, 1)
    extreme = _clamp(0.08 * rain_prob + 0.35 * thunder_prob, 0, 1)
    total = light + moderate + heavy + extreme
    return {
        "light": round(light / total, 4),
        "moderate": round(moderate / total, 4),
        "heavy": round(heavy / total, 4),
        "extreme": round(extreme / total, 4),
    }


def _counterfactuals(obs: dict[str, Any], rain_prob: float) -> list[dict[str, Any]]:
    return [
        {"change": "If pressure increases by 4 hPa", "impact_on_rain_probability": round(-0.08 * rain_prob, 4)},
        {"change": "If humidity drops by 10%", "impact_on_rain_probability": round(-0.12 * rain_prob, 4)},
        {"change": "If cloud cover increases by 15%", "impact_on_rain_probability": round(0.09 * (1 - rain_prob), 4)},
    ]


def _feature_attributions(feature_scores: dict[str, float]) -> list[dict[str, Any]]:
    ranked = sorted(feature_scores.items(), key=lambda kv: abs(kv[1]), reverse=True)
    return [
        {"factor": name, "impact": round(abs(val), 3), "direction": "increases" if val >= 0 else "decreases"}
        for name, val in ranked[:6]
    ]


def _horizon_projection(
    obs: dict[str, Any],
    location: str,
    risk_mode: str,
    thresholds: dict[str, float],
    knowledge_base: dict[str, Any],
) -> list[dict[str, Any]]:
    horizons: list[dict[str, Any]] = []
    for horizon in DEFAULT_HORIZONS:
        core = infer_weather(
            obs,
            location=location,
            horizon_hours=horizon,
            risk_mode=risk_mode,
            custom_thresholds=thresholds,
            include_horizons=False,
            knowledge_base=knowledge_base,
        )
        horizons.append(
            {
                "horizon_hours": horizon,
                "predicted_condition": core["predicted_condition"],
                "rain_probability": core["rain_probability"],
                "expected_rainfall_mm": core["expected_rainfall_mm"],
                "confidence_score": core["confidence_score"],
            }
        )
    return horizons


def _climatology_smoothing(probabilities: dict[str, float], location: str, month: int) -> tuple[dict[str, float], dict[str, Any]]:
    climatology = climatology_distribution(location, month)
    sample_count = climatology["sample_count"]
    alpha = _clamp(sample_count / 2000, 0.05, 0.16)
    smoothed: dict[str, float] = {}
    for condition, prob in probabilities.items():
        prior = climatology["distribution"].get(condition, prob)
        smoothed[condition] = _clamp((1 - alpha) * prob + alpha * prior, 0.0001, 0.999)
    total = sum(smoothed.values())
    return (
        {k: v / total for k, v in smoothed.items()},
        {"city": climatology["city"], "sample_count": sample_count, "blend_alpha": round(alpha, 4)},
    )


def infer_weather(
    obs: dict[str, Any],
    *,
    location: str,
    horizon_hours: int,
    risk_mode: str = "general",
    custom_thresholds: dict[str, float] | None = None,
    include_horizons: bool = True,
    knowledge_base: dict[str, Any] | None = None,
) -> dict[str, Any]:
    custom_thresholds = custom_thresholds or {}
    knowledge_base = knowledge_base or {}
    base_priors = knowledge_base.get("base_priors", DEFAULT_BASE_PRIORS)
    seasonal_multipliers = knowledge_base.get("seasonal_multipliers", DEFAULT_SEASONAL_MULTIPLIERS)
    terrain_multipliers = knowledge_base.get("terrain_multipliers", DEFAULT_TERRAIN_MULTIPLIERS)
    climate_zone_multipliers = knowledge_base.get("climate_zone_multipliers", DEFAULT_CLIMATE_ZONE_MULTIPLIERS)
    monthly_raw = knowledge_base.get("monthly_multipliers", DEFAULT_MONTHLY_MULTIPLIERS)
    monthly_multipliers = {int(k): v for k, v in monthly_raw.items()}
    risk_mode_alert_weights = knowledge_base.get("risk_mode_alert_weights", DEFAULT_RISK_MODE_ALERT_WEIGHTS)
    risk_mode_thresholds = knowledge_base.get("risk_mode_thresholds", DEFAULT_RISK_MODE_THRESHOLDS)

    quality = data_quality(obs)
    baseline = apply_historical_baseline(obs, infer_climate_zone(location), obs["month"])

    scores = {condition: math.log(base_priors.get(condition, DEFAULT_BASE_PRIORS[condition])) for condition in CONDITIONS}
    feature_scores = _feature_contributions(obs, baseline)
    scores, impact_trace, climate_zone = _apply_knowledge_multipliers(
        scores,
        obs,
        location,
        feature_scores,
        seasonal_multipliers=seasonal_multipliers,
        terrain_multipliers=terrain_multipliers,
        climate_zone_multipliers=climate_zone_multipliers,
        monthly_multipliers=monthly_multipliers,
    )
    scores, rule_trace = _apply_rules(scores, obs)

    horizon_factor = _clamp(horizon_hours / 6, 0.5, 3.7)
    scores["rain"] += math.log(1 + 0.08 * horizon_factor)
    scores["thunderstorm"] += math.log(1 + 0.1 * max(0, horizon_factor - 1))

    probabilities = _softmax(scores)
    probabilities = _dynamic_transition(probabilities, horizon_hours)
    probabilities = _calibrate(probabilities, quality["sensor_reliability"])
    probabilities, climatology_meta = _climatology_smoothing(probabilities, location, obs["month"])

    rain_prob = probabilities["rain"] + 0.45 * probabilities["drizzle"] + 0.5 * probabilities["thunderstorm"]
    rain_prob = _clamp(rain_prob, 0, 1)
    confidence = _confidence(probabilities, quality["uncertainty_penalty"])
    expected_rainfall = _expected_rainfall_mm(obs, rain_prob, probabilities["thunderstorm"], horizon_hours)
    predicted_condition = max(probabilities, key=probabilities.get)

    top_factor_items = sorted(impact_trace.items(), key=lambda kv: abs(kv[1]), reverse=True)[:6]
    key_factors = []
    for key, val in top_factor_items:
        label = key.replace("feature::", "").replace("rule::", "")
        key_factors.append({"factor": label, "impact": round(abs(val), 3), "direction": "increases" if val >= 0 else "decreases"})

    horizons = _horizon_projection(obs, location, risk_mode, custom_thresholds, knowledge_base) if include_horizons else []
    scenarios = _scenario_simulation(rain_prob, expected_rainfall)
    events = _event_probabilities(probabilities, rain_prob, horizon_hours)
    bands = _intensity_bands(rain_prob, probabilities["thunderstorm"])
    counterfactuals = _counterfactuals(obs, rain_prob)

    explanation = (
        f"{predicted_condition} is most likely at {round(max(probabilities.values()) * 100)}% confidence weight. "
        f"Rain probability is {rain_prob:.2f} with expected rainfall {expected_rainfall} mm over {horizon_hours}h. "
        f"Climate zone: {climate_zone}. Climatology blend alpha: {climatology_meta['blend_alpha']}."
    )

    return {
        "predicted_condition": predicted_condition,
        "condition_probabilities": probabilities,
        "rain_probability": round(rain_prob, 4),
        "expected_rainfall_mm": expected_rainfall,
        "confidence_score": round(confidence, 4),
        "alert_level": _alert_level(
            rain_prob,
            probabilities["thunderstorm"],
            probabilities["windy"],
            risk_mode,
            custom_thresholds,
            risk_mode_alert_weights=risk_mode_alert_weights,
            risk_mode_thresholds=risk_mode_thresholds,
        ),
        "expert_recommendations": _recommendations(
            risk_mode,
            rain_prob,
            probabilities["thunderstorm"],
            probabilities["fog"],
            probabilities["windy"],
        ),
        "key_factors": key_factors,
        "feature_attributions": _feature_attributions(feature_scores),
        "rule_trace": rule_trace,
        "counterfactuals": counterfactuals,
        "scenarios": scenarios,
        "horizons": horizons,
        "event_probabilities": events,
        "intensity_bands": bands,
        "data_quality": quality,
        "climatology_meta": climatology_meta,
        "explanation": explanation,
    }

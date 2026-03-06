from __future__ import annotations

import math
import random
from typing import Any

from .knowledge_base import BASE_PRIORS, SEASONAL_MULTIPLIERS, TERRAIN_MULTIPLIERS, expert_rules


CONDITIONS = list(BASE_PRIORS.keys())


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    ceiling = max(scores.values())
    exp_scores = {key: math.exp(val - ceiling) for key, val in scores.items()}
    total = sum(exp_scores.values())
    return {key: val / total for key, val in exp_scores.items()}


def _feature_contributions(obs: dict[str, Any]) -> dict[str, float]:
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
            + 1.8 * cloud
            + 0.25 * recent_rain
            + (1008 - pressure) * 0.01
            + 0.4 * evening_convective
            - 0.015 * max(0, uv - 7)
        ),
        "drizzle": (
            1.6 * humidity
            + 1.4 * cloud
            + 0.18 * recent_rain
            - 0.008 * abs(pressure - 1012)
            - 0.02 * max(0, wind - 30)
        ),
        "thunderstorm": (
            0.06 * max(0, temp - 24)
            + 1.3 * humidity
            + 0.95 * cloud
            + (1005 - pressure) * 0.018
            + 0.05 * wind
            + 0.5 * evening_convective
        ),
        "fog": (
            1.45 * humidity
            + 0.6 * cloud
            + 0.25 * night
            - 0.05 * wind
            + 0.12 * max(0, 4 - dew_gap)
            + 0.15 * max(0, 5 - visibility)
        ),
        "windy": (
            0.09 * wind + (1008 - pressure) * 0.01 + 0.12 * cloud - 0.02 * humidity + 0.08 * evening_convective
        ),
        "clear": (
            1.7 * (1 - cloud)
            + 1.2 * (1 - humidity)
            + 0.04 * uv
            + 0.01 * max(0, pressure - 1012)
            - 0.05 * recent_rain
        ),
        "cloudy": (
            1.85 * cloud
            + 0.8 * humidity
            + 0.01 * max(0, 1015 - pressure)
            - 0.02 * uv
            + 0.02 * max(0, 28 - temp)
        ),
    }


def _confidence(probabilities: dict[str, float], missing: float) -> float:
    entropy = -sum(p * math.log(p + 1e-12) for p in probabilities.values())
    max_entropy = math.log(len(probabilities))
    certainty = 1 - entropy / max_entropy
    return _clamp(0.25 + 0.75 * certainty - 0.1 * missing, 0.05, 0.99)


def _recommendations(rain_prob: float, thunder_prob: float, fog_prob: float, wind_prob: float) -> list[str]:
    recs: list[str] = []
    if rain_prob >= 0.55:
        recs.append("Carry rain protection and avoid waterlogged routes.")
    if thunder_prob >= 0.4:
        recs.append("Expect possible lightning; avoid open fields and unsecured rooftops.")
    if fog_prob >= 0.35:
        recs.append("Use low-beam headlights and maintain larger following distance.")
    if wind_prob >= 0.45:
        recs.append("Secure loose outdoor items and avoid parking under weak structures.")
    if not recs:
        recs.append("No major weather hazard likely in the selected horizon.")
    return recs


def _alert_level(rain_prob: float, thunder_prob: float, wind_prob: float) -> str:
    risk_score = 0.45 * rain_prob + 0.4 * thunder_prob + 0.15 * wind_prob
    if risk_score >= 0.72:
        return "severe"
    if risk_score >= 0.52:
        return "high"
    if risk_score >= 0.3:
        return "moderate"
    return "low"


def _expected_rainfall_mm(obs: dict[str, Any], rain_prob: float, thunder_prob: float) -> float:
    samples = []
    humidity = obs["humidity_pct"] / 100
    cloud = obs["cloud_cover_pct"] / 100
    trend_boost = 1.2 if obs["pressure_trend"] == "falling" else 1.0
    for _ in range(400):
        intensity = random.gammavariate(1.5 + 2 * thunder_prob, 2.5 + 1.5 * humidity)
        base = intensity * rain_prob * cloud * trend_boost
        noise = random.uniform(-0.4, 0.8)
        samples.append(max(0.0, base + noise))
    return round(sum(samples) / len(samples), 2)


def infer_weather(obs: dict[str, Any], horizon_hours: int) -> dict[str, Any]:
    scores = {cond: math.log(BASE_PRIORS[cond]) for cond in CONDITIONS}
    feature_scores = _feature_contributions(obs)
    impact_trace: dict[str, float] = {}

    for cond in CONDITIONS:
        season_mult = SEASONAL_MULTIPLIERS.get(obs["season"], {}).get(cond, 1.0)
        terrain_mult = TERRAIN_MULTIPLIERS.get(obs["terrain"], {}).get(cond, 1.0)
        combined = feature_scores[cond] * season_mult * terrain_mult
        scores[cond] += combined
        impact_trace[f"feature::{cond}"] = combined

    rule_reasons: list[str] = []
    for effect in expert_rules(obs):
        delta = math.log(effect.weight)
        scores[effect.condition] += delta
        impact_trace[f"rule::{effect.reason}"] = delta
        rule_reasons.append(effect.reason)

    hours_factor = _clamp(horizon_hours / 6, 0.5, 3.5)
    scores["rain"] += math.log(1 + 0.08 * hours_factor)
    scores["thunderstorm"] += math.log(1 + 0.1 * max(0, hours_factor - 1))

    probabilities = _softmax(scores)
    rain_prob = probabilities["rain"] + 0.45 * probabilities["drizzle"] + 0.5 * probabilities["thunderstorm"]
    rain_prob = _clamp(rain_prob, 0, 1)
    confidence = _confidence(probabilities, missing=0.0)
    expected_rainfall = _expected_rainfall_mm(obs, rain_prob=rain_prob, thunder_prob=probabilities["thunderstorm"])

    top_factor_items = sorted(impact_trace.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    top_factors = []
    for key, val in top_factor_items:
        label = key.replace("feature::", "").replace("rule::", "")
        top_factors.append({"factor": label, "impact": round(abs(val), 3), "direction": "increases" if val >= 0 else "decreases"})

    predicted_condition = max(probabilities, key=probabilities.get)
    explanation = (
        f"Most likely condition is {predicted_condition}. "
        f"Rain probability is {rain_prob:.2f} over {horizon_hours}h. "
        f"Top drivers include {', '.join([item['factor'] for item in top_factors[:3]])}."
    )
    if rule_reasons:
        explanation += f" Expert rules fired: {'; '.join(rule_reasons[:3])}."

    return {
        "predicted_condition": predicted_condition,
        "condition_probabilities": probabilities,
        "rain_probability": round(rain_prob, 4),
        "expected_rainfall_mm": expected_rainfall,
        "confidence_score": round(confidence, 4),
        "alert_level": _alert_level(rain_prob, probabilities["thunderstorm"], probabilities["windy"]),
        "expert_recommendations": _recommendations(
            rain_prob,
            probabilities["thunderstorm"],
            probabilities["fog"],
            probabilities["windy"],
        ),
        "key_factors": top_factors,
        "explanation": explanation,
    }


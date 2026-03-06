from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleEffect:
    condition: str
    weight: float
    reason: str


BASE_PRIORS = {
    "clear": 0.22,
    "cloudy": 0.2,
    "rain": 0.2,
    "drizzle": 0.1,
    "thunderstorm": 0.09,
    "fog": 0.09,
    "windy": 0.1,
}


SEASONAL_MULTIPLIERS = {
    "winter": {"fog": 1.55, "clear": 1.15, "rain": 0.85, "thunderstorm": 0.75},
    "spring": {"cloudy": 1.15, "rain": 1.1, "clear": 1.05},
    "summer": {"clear": 1.2, "thunderstorm": 1.2, "drizzle": 0.8},
    "monsoon": {"rain": 1.8, "drizzle": 1.35, "thunderstorm": 1.3, "clear": 0.7},
    "autumn": {"clear": 1.15, "cloudy": 1.1, "fog": 1.1},
}


TERRAIN_MULTIPLIERS = {
    "coastal": {"rain": 1.2, "drizzle": 1.25, "windy": 1.1},
    "plains": {"fog": 1.15, "clear": 1.05},
    "urban": {"cloudy": 1.08, "fog": 1.08},
    "mountain": {"rain": 1.2, "thunderstorm": 1.25, "fog": 1.15},
    "forest": {"rain": 1.12, "fog": 1.18},
    "desert": {"clear": 1.35, "rain": 0.65, "drizzle": 0.55},
}


def expert_rules(obs: dict) -> list[RuleEffect]:
    effects: list[RuleEffect] = []

    if obs["humidity_pct"] > 80 and obs["cloud_cover_pct"] > 70:
        effects.append(RuleEffect("rain", 1.2, "High humidity + dense cloud cover strongly supports rain"))
    if obs["pressure_hpa"] < 1000 and obs["pressure_trend"] == "falling":
        effects.append(RuleEffect("thunderstorm", 1.35, "Falling low pressure can trigger convective activity"))
    if obs["temperature_c"] - obs["dew_point_c"] <= 2 and obs["visibility_km"] < 4:
        effects.append(RuleEffect("fog", 1.55, "Small temp-dew gap and low visibility indicate fog formation"))
    if obs["wind_kph"] > 35:
        effects.append(RuleEffect("windy", 1.45, "Sustained high wind speed indicates windy conditions"))
    if obs["uv_index"] > 8 and obs["cloud_cover_pct"] < 30 and obs["humidity_pct"] < 55:
        effects.append(RuleEffect("clear", 1.35, "High UV and low cloudiness favor clear sky"))
    if obs["recent_rain_mm"] > 6:
        effects.append(RuleEffect("drizzle", 1.2, "Recent rain persistence increases ongoing drizzle likelihood"))
        effects.append(RuleEffect("rain", 1.15, "Recent rainfall raises short-term rain persistence"))
    if 14 <= obs["hour_24"] <= 19 and obs["temperature_c"] > 30 and obs["humidity_pct"] > 65:
        effects.append(RuleEffect("thunderstorm", 1.28, "Late-day heat and humidity increase storm risk"))

    return effects


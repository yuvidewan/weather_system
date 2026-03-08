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

CLIMATE_ZONE_BY_LOCATION_HINT = {
    "mumbai": "humid_tropical",
    "chennai": "humid_tropical",
    "kolkata": "humid_tropical",
    "delhi": "continental",
    "new delhi": "continental",
    "jaipur": "arid",
    "leh": "highland",
    "shimla": "highland",
    "bangalore": "plateau",
    "bengaluru": "plateau",
    "hyderabad": "plateau",
    "goa": "humid_tropical",
}

CLIMATE_ZONE_MULTIPLIERS = {
    "humid_tropical": {"rain": 1.26, "drizzle": 1.15, "thunderstorm": 1.1, "clear": 0.9},
    "continental": {"clear": 1.08, "fog": 1.18, "rain": 0.96},
    "arid": {"clear": 1.3, "rain": 0.62, "drizzle": 0.5, "fog": 0.88},
    "highland": {"fog": 1.24, "rain": 1.12, "thunderstorm": 1.08},
    "plateau": {"thunderstorm": 1.14, "clear": 1.06, "drizzle": 0.9},
}

MONTHLY_MULTIPLIERS = {
    1: {"fog": 1.18, "rain": 0.88, "clear": 1.08},
    2: {"fog": 1.12, "clear": 1.05},
    3: {"cloudy": 1.05, "thunderstorm": 1.06},
    4: {"thunderstorm": 1.12, "rain": 1.06},
    5: {"thunderstorm": 1.2, "clear": 1.05},
    6: {"rain": 1.22, "drizzle": 1.18},
    7: {"rain": 1.34, "drizzle": 1.24, "thunderstorm": 1.12},
    8: {"rain": 1.31, "drizzle": 1.2, "cloudy": 1.08},
    9: {"rain": 1.15, "cloudy": 1.12},
    10: {"clear": 1.1, "cloudy": 1.05},
    11: {"clear": 1.12, "fog": 1.1},
    12: {"fog": 1.2, "clear": 1.08, "rain": 0.85},
}

RISK_MODE_ALERT_WEIGHTS = {
    "general": {"rain": 0.45, "thunderstorm": 0.4, "windy": 0.15},
    "agriculture": {"rain": 0.55, "thunderstorm": 0.25, "windy": 0.2},
    "travel": {"rain": 0.35, "thunderstorm": 0.3, "windy": 0.2},
    "events": {"rain": 0.5, "thunderstorm": 0.35, "windy": 0.15},
    "logistics": {"rain": 0.4, "thunderstorm": 0.25, "windy": 0.35},
}

RISK_MODE_THRESHOLDS = {
    "general": {"moderate": 0.3, "high": 0.52, "severe": 0.72},
    "agriculture": {"moderate": 0.25, "high": 0.47, "severe": 0.66},
    "travel": {"moderate": 0.22, "high": 0.4, "severe": 0.6},
    "events": {"moderate": 0.25, "high": 0.43, "severe": 0.62},
    "logistics": {"moderate": 0.28, "high": 0.45, "severe": 0.64},
}


def infer_climate_zone(location: str) -> str:
    hint = location.strip().lower()
    return CLIMATE_ZONE_BY_LOCATION_HINT.get(hint, "continental")


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
    if obs["pressure_hpa"] < 995 and obs["wind_kph"] > 28:
        effects.append(RuleEffect("thunderstorm", 1.22, "Deep low pressure and elevated winds support storm growth"))
    if obs["humidity_pct"] < 38 and obs["cloud_cover_pct"] < 25:
        effects.append(RuleEffect("clear", 1.24, "Dry air and low cloud cover reinforce clear weather"))
    if obs["visibility_km"] < 2 and obs["wind_kph"] < 12 and obs["hour_24"] <= 8:
        effects.append(RuleEffect("fog", 1.27, "Low morning mixing and poor visibility increase fog likelihood"))
    if obs["temperature_c"] > 35 and obs["humidity_pct"] > 55 and obs["cloud_cover_pct"] > 60:
        effects.append(RuleEffect("thunderstorm", 1.2, "Hot humid boundary layer plus clouds supports convection"))
    if obs["pressure_trend"] == "rising" and obs["pressure_hpa"] > 1014 and obs["cloud_cover_pct"] < 35:
        effects.append(RuleEffect("clear", 1.18, "Rising pressure with sparse clouds favors clearing"))
    if obs["wind_kph"] > 45:
        effects.append(RuleEffect("windy", 1.38, "Very strong winds indicate windy regime"))
    if obs["recent_rain_mm"] > 15:
        effects.append(RuleEffect("rain", 1.2, "Heavy recent rain indicates saturated wet pattern persistence"))
    if obs["recent_rain_mm"] == 0 and obs["humidity_pct"] < 45 and obs["uv_index"] > 7:
        effects.append(RuleEffect("clear", 1.14, "Dry recent conditions and strong UV support stable clear state"))
    if obs["humidity_pct"] > 90 and obs["temperature_c"] < 16:
        effects.append(RuleEffect("fog", 1.2, "Cold saturated air mass is favorable for fog"))
    if obs["cloud_cover_pct"] > 92 and obs["wind_kph"] < 18 and obs["humidity_pct"] > 82:
        effects.append(RuleEffect("drizzle", 1.18, "Thick low cloud and moist calm flow supports drizzle"))
    if obs["pressure_hpa"] > 1020 and obs["humidity_pct"] < 60 and obs["wind_kph"] < 20:
        effects.append(RuleEffect("clear", 1.16, "High pressure and modest wind usually stabilize clear conditions"))

    return effects

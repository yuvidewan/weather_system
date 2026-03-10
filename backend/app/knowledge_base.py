from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuleEffect:
    condition: str
    weight: float
    reason: str


BASE_PRIORS = {
    "clear": 0.2,
    "cloudy": 0.21,
    "rain": 0.19,
    "drizzle": 0.1,
    "thunderstorm": 0.1,
    "fog": 0.09,
    "windy": 0.11,
}


SEASONAL_MULTIPLIERS = {
    "winter": {"clear": 1.12, "cloudy": 1.04, "rain": 0.8, "drizzle": 0.92, "thunderstorm": 0.72, "fog": 1.5, "windy": 0.96},
    "spring": {"clear": 1.02, "cloudy": 1.12, "rain": 1.08, "drizzle": 1.03, "thunderstorm": 1.08, "fog": 0.92, "windy": 1.03},
    "summer": {"clear": 1.16, "cloudy": 0.96, "rain": 0.94, "drizzle": 0.78, "thunderstorm": 1.22, "fog": 0.74, "windy": 1.07},
    "monsoon": {"clear": 0.62, "cloudy": 1.2, "rain": 1.78, "drizzle": 1.3, "thunderstorm": 1.24, "fog": 0.95, "windy": 1.06},
    "autumn": {"clear": 1.14, "cloudy": 1.09, "rain": 0.97, "drizzle": 0.92, "thunderstorm": 0.93, "fog": 1.08, "windy": 1.0},
}


TERRAIN_MULTIPLIERS = {
    "coastal": {"clear": 0.92, "cloudy": 1.08, "rain": 1.24, "drizzle": 1.28, "thunderstorm": 1.06, "fog": 1.05, "windy": 1.14},
    "plains": {"clear": 1.04, "cloudy": 1.02, "rain": 0.98, "drizzle": 0.97, "thunderstorm": 0.98, "fog": 1.18, "windy": 1.0},
    "urban": {"clear": 1.01, "cloudy": 1.08, "rain": 1.0, "drizzle": 0.95, "thunderstorm": 1.06, "fog": 1.08, "windy": 1.02},
    "mountain": {"clear": 0.94, "cloudy": 1.04, "rain": 1.18, "drizzle": 1.1, "thunderstorm": 1.22, "fog": 1.2, "windy": 1.06},
    "forest": {"clear": 0.96, "cloudy": 1.04, "rain": 1.14, "drizzle": 1.08, "thunderstorm": 1.07, "fog": 1.18, "windy": 0.96},
    "desert": {"clear": 1.32, "cloudy": 0.82, "rain": 0.64, "drizzle": 0.52, "thunderstorm": 0.88, "fog": 0.82, "windy": 1.14},
}


CLIMATE_ZONE_BY_LOCATION_HINT = {
    "delhi": "continental",
    "new delhi": "continental",
    "lucknow": "continental",
    "kanpur": "continental",
    "patna": "continental",
    "nagpur": "continental",
    "vadodara": "continental",
    "kolkata": "humid_tropical",
    "calcutta": "humid_tropical",
    "mumbai": "humid_tropical",
    "bombay": "humid_tropical",
    "chennai": "humid_tropical",
    "madras": "humid_tropical",
    "surat": "humid_tropical",
    "kochi": "humid_tropical",
    "cochin": "humid_tropical",
    "goa": "humid_tropical",
    "panaji": "humid_tropical",
    "bengaluru": "plateau",
    "bangalore": "plateau",
    "hyderabad": "plateau",
    "pune": "plateau",
    "indore": "plateau",
    "bhopal": "plateau",
    "coimbatore": "plateau",
    "jaipur": "arid",
    "ahmedabad": "arid",
    "shimla": "highland",
    "leh": "highland",
}


CLIMATE_ZONE_MULTIPLIERS = {
    "humid_tropical": {"clear": 0.9, "cloudy": 1.08, "rain": 1.24, "drizzle": 1.12, "thunderstorm": 1.08, "fog": 0.94, "windy": 1.02},
    "continental": {"clear": 1.08, "cloudy": 1.02, "rain": 0.96, "drizzle": 0.96, "thunderstorm": 1.0, "fog": 1.18, "windy": 1.0},
    "arid": {"clear": 1.28, "cloudy": 0.86, "rain": 0.62, "drizzle": 0.5, "thunderstorm": 0.9, "fog": 0.88, "windy": 1.12},
    "highland": {"clear": 0.95, "cloudy": 1.04, "rain": 1.1, "drizzle": 1.04, "thunderstorm": 1.1, "fog": 1.24, "windy": 1.06},
    "plateau": {"clear": 1.04, "cloudy": 0.98, "rain": 1.0, "drizzle": 0.9, "thunderstorm": 1.16, "fog": 0.96, "windy": 1.02},
}


MONTHLY_MULTIPLIERS = {
    1: {"clear": 1.1, "cloudy": 1.0, "rain": 0.84, "drizzle": 0.92, "thunderstorm": 0.72, "fog": 1.22, "windy": 0.98},
    2: {"clear": 1.08, "cloudy": 1.02, "rain": 0.88, "drizzle": 0.96, "thunderstorm": 0.78, "fog": 1.16, "windy": 0.99},
    3: {"clear": 1.04, "cloudy": 1.08, "rain": 1.0, "drizzle": 0.98, "thunderstorm": 1.04, "fog": 0.95, "windy": 1.01},
    4: {"clear": 1.01, "cloudy": 1.08, "rain": 1.06, "drizzle": 1.0, "thunderstorm": 1.14, "fog": 0.88, "windy": 1.03},
    5: {"clear": 1.05, "cloudy": 0.98, "rain": 1.02, "drizzle": 0.88, "thunderstorm": 1.22, "fog": 0.82, "windy": 1.08},
    6: {"clear": 0.86, "cloudy": 1.12, "rain": 1.24, "drizzle": 1.18, "thunderstorm": 1.15, "fog": 0.9, "windy": 1.04},
    7: {"clear": 0.78, "cloudy": 1.14, "rain": 1.34, "drizzle": 1.24, "thunderstorm": 1.12, "fog": 0.96, "windy": 1.06},
    8: {"clear": 0.8, "cloudy": 1.16, "rain": 1.3, "drizzle": 1.18, "thunderstorm": 1.08, "fog": 0.98, "windy": 1.05},
    9: {"clear": 0.92, "cloudy": 1.14, "rain": 1.16, "drizzle": 1.06, "thunderstorm": 1.01, "fog": 1.0, "windy": 1.02},
    10: {"clear": 1.08, "cloudy": 1.06, "rain": 0.98, "drizzle": 0.96, "thunderstorm": 0.96, "fog": 1.02, "windy": 1.0},
    11: {"clear": 1.12, "cloudy": 1.02, "rain": 0.9, "drizzle": 0.92, "thunderstorm": 0.84, "fog": 1.12, "windy": 0.99},
    12: {"clear": 1.1, "cloudy": 1.0, "rain": 0.82, "drizzle": 0.9, "thunderstorm": 0.74, "fog": 1.2, "windy": 0.98},
}


RISK_MODE_ALERT_WEIGHTS = {
    "general": {"rain": 0.44, "thunderstorm": 0.4, "windy": 0.16},
    "agriculture": {"rain": 0.57, "thunderstorm": 0.22, "windy": 0.21},
    "travel": {"rain": 0.34, "thunderstorm": 0.31, "windy": 0.23},
    "events": {"rain": 0.49, "thunderstorm": 0.36, "windy": 0.15},
    "logistics": {"rain": 0.39, "thunderstorm": 0.24, "windy": 0.37},
}


RISK_MODE_THRESHOLDS = {
    "general": {"moderate": 0.29, "high": 0.5, "severe": 0.7},
    "agriculture": {"moderate": 0.24, "high": 0.45, "severe": 0.64},
    "travel": {"moderate": 0.22, "high": 0.39, "severe": 0.58},
    "events": {"moderate": 0.24, "high": 0.42, "severe": 0.61},
    "logistics": {"moderate": 0.27, "high": 0.44, "severe": 0.63},
}


EXPERT_RULES: tuple[dict[str, Any], ...] = (
    {
        "condition": "rain",
        "weight": 1.28,
        "reason": "Saturated air, deep cloud cover, and low pressure strongly favor organized rainfall.",
        "all_of": (
            {"field": "humidity_pct", "op": "gte", "value": 82},
            {"field": "cloud_cover_pct", "op": "gte", "value": 78},
            {"field": "pressure_hpa", "op": "lte", "value": 1006},
        ),
    },
    {
        "condition": "rain",
        "weight": 1.22,
        "reason": "Monsoon-period wet ground and thick cloud usually sustain further rain in the near term.",
        "all_of": (
            {"field": "season", "op": "eq", "value": "monsoon"},
            {"field": "recent_rain_mm", "op": "gte", "value": 10},
            {"field": "cloud_cover_pct", "op": "gte", "value": 72},
        ),
    },
    {
        "condition": "rain",
        "weight": 1.18,
        "reason": "Warm stratiform cloud shields with strong moisture content support steady rain.",
        "all_of": (
            {"field": "cloud_cover_pct", "op": "gte", "value": 88},
            {"field": "humidity_pct", "op": "gte", "value": 80},
            {"field": "wind_kph", "op": "between", "value": [8, 28]},
            {"field": "pressure_hpa", "op": "between", "value": [996, 1008]},
        ),
    },
    {
        "condition": "rain",
        "weight": 1.16,
        "reason": "Very wet antecedent conditions make repeated showers more persistent.",
        "all_of": (
            {"field": "recent_rain_mm", "op": "gte", "value": 18},
            {"field": "humidity_pct", "op": "gte", "value": 80},
        ),
    },
    {
        "condition": "drizzle",
        "weight": 1.32,
        "reason": "Calm saturated low cloud with a tiny dew-point spread is classic drizzle or misty light rain.",
        "all_of": (
            {"field": "humidity_pct", "op": "gte", "value": 86},
            {"field": "cloud_cover_pct", "op": "gte", "value": 90},
            {"field": "wind_kph", "op": "lte", "value": 18},
            {"field": "dew_point_spread_c", "op": "lte", "value": 2.4},
        ),
    },
    {
        "condition": "drizzle",
        "weight": 1.2,
        "reason": "Cool marine moisture with moderate onshore flow often produces shallow drizzle rather than convective rain.",
        "all_of": (
            {"field": "terrain", "op": "eq", "value": "coastal"},
            {"field": "temperature_c", "op": "lte", "value": 24},
            {"field": "humidity_pct", "op": "gte", "value": 88},
            {"field": "wind_kph", "op": "between", "value": [6, 20]},
        ),
    },
    {
        "condition": "drizzle",
        "weight": 1.18,
        "reason": "Night-time post-rain saturation under thick cloud often degrades into lingering drizzle.",
        "all_of": (
            {"field": "recent_rain_mm", "op": "gte", "value": 6},
            {"field": "cloud_cover_pct", "op": "gte", "value": 80},
            {"field": "is_night", "op": "eq", "value": 1},
            {"field": "wind_kph", "op": "lte", "value": 18},
        ),
    },
    {
        "condition": "thunderstorm",
        "weight": 1.34,
        "reason": "Warm humid afternoon air with falling pressure strongly supports convective storm growth.",
        "all_of": (
            {"field": "temperature_c", "op": "gte", "value": 31},
            {"field": "humidity_pct", "op": "gte", "value": 68},
            {"field": "pressure_trend", "op": "eq", "value": "falling"},
            {"field": "hour_24", "op": "between", "value": [13, 20]},
        ),
    },
    {
        "condition": "thunderstorm",
        "weight": 1.36,
        "reason": "Deep low pressure with abundant moisture and cloud cover is a strong storm signature.",
        "all_of": (
            {"field": "pressure_hpa", "op": "lte", "value": 995},
            {"field": "humidity_pct", "op": "gte", "value": 70},
            {"field": "cloud_cover_pct", "op": "gte", "value": 65},
        ),
    },
    {
        "condition": "thunderstorm",
        "weight": 1.24,
        "reason": "Extreme heat plus high dew point raises convective instability and thunderstorm risk.",
        "all_of": (
            {"field": "temperature_c", "op": "gte", "value": 36},
            {"field": "dew_point_c", "op": "gte", "value": 24},
            {"field": "cloud_cover_pct", "op": "gte", "value": 55},
        ),
    },
    {
        "condition": "thunderstorm",
        "weight": 1.18,
        "reason": "Mountain terrain plus humid afternoon uplift often triggers scattered convection.",
        "all_of": (
            {"field": "terrain", "op": "eq", "value": "mountain"},
            {"field": "humidity_pct", "op": "gte", "value": 72},
            {"field": "cloud_cover_pct", "op": "gte", "value": 62},
            {"field": "hour_24", "op": "between", "value": [12, 19]},
        ),
    },
    {
        "condition": "thunderstorm",
        "weight": 1.18,
        "reason": "Gusty moist flow under falling pressure can indicate an organized squall line environment.",
        "all_of": (
            {"field": "wind_kph", "op": "gte", "value": 28},
            {"field": "cloud_cover_pct", "op": "gte", "value": 78},
            {"field": "pressure_trend", "op": "eq", "value": "falling"},
            {"field": "humidity_pct", "op": "gte", "value": 70},
        ),
    },
    {
        "condition": "fog",
        "weight": 1.42,
        "reason": "Small dew-point spread, light wind, and poor night-time visibility strongly indicate fog formation.",
        "all_of": (
            {"field": "dew_point_spread_c", "op": "lte", "value": 1.8},
            {"field": "wind_kph", "op": "lte", "value": 10},
            {"field": "visibility_km", "op": "lte", "value": 4},
            {"field": "hour_24", "op": "between", "value": [0, 8]},
        ),
    },
    {
        "condition": "fog",
        "weight": 1.28,
        "reason": "Winter plains often trap saturated air overnight, increasing dense fog risk.",
        "all_of": (
            {"field": "season", "op": "eq", "value": "winter"},
            {"field": "terrain", "op": "in", "value": ["plains", "urban"]},
            {"field": "humidity_pct", "op": "gte", "value": 88},
            {"field": "visibility_km", "op": "lte", "value": 5},
            {"field": "wind_kph", "op": "lte", "value": 12},
        ),
    },
    {
        "condition": "fog",
        "weight": 1.2,
        "reason": "Cool moist mountain air with weak mixing commonly favors valley fog or cloud immersion.",
        "all_of": (
            {"field": "terrain", "op": "eq", "value": "mountain"},
            {"field": "temperature_c", "op": "lte", "value": 14},
            {"field": "humidity_pct", "op": "gte", "value": 85},
            {"field": "visibility_km", "op": "lte", "value": 6},
        ),
    },
    {
        "condition": "fog",
        "weight": 1.24,
        "reason": "Cold dawn saturation with very little temperature-dew spread is a strong dense fog signal.",
        "all_of": (
            {"field": "temperature_c", "op": "between", "value": [8, 18]},
            {"field": "humidity_pct", "op": "gte", "value": 92},
            {"field": "hour_24", "op": "between", "value": [4, 8]},
            {"field": "dew_point_spread_c", "op": "lte", "value": 1.2},
        ),
    },
    {
        "condition": "clear",
        "weight": 1.34,
        "reason": "High pressure, low humidity, and limited cloud cover are classic subsidence-clearing conditions.",
        "all_of": (
            {"field": "pressure_hpa", "op": "gte", "value": 1018},
            {"field": "pressure_trend", "op": "eq", "value": "rising"},
            {"field": "cloud_cover_pct", "op": "lte", "value": 28},
            {"field": "humidity_pct", "op": "lte", "value": 50},
        ),
    },
    {
        "condition": "clear",
        "weight": 1.24,
        "reason": "Dry air, strong visibility, and no recent rain point to a stable clear regime.",
        "all_of": (
            {"field": "humidity_pct", "op": "lte", "value": 36},
            {"field": "cloud_cover_pct", "op": "lte", "value": 20},
            {"field": "visibility_km", "op": "gte", "value": 12},
            {"field": "recent_rain_mm", "op": "lte", "value": 0.5},
        ),
    },
    {
        "condition": "clear",
        "weight": 1.16,
        "reason": "A rising-pressure post-frontal pattern often supports improving visibility and clearer skies.",
        "all_of": (
            {"field": "pressure_trend", "op": "eq", "value": "rising"},
            {"field": "wind_kph", "op": "between", "value": [10, 32]},
            {"field": "cloud_cover_pct", "op": "lte", "value": 35},
            {"field": "visibility_km", "op": "gte", "value": 10},
        ),
    },
    {
        "condition": "clear",
        "weight": 1.16,
        "reason": "Winter high pressure with sparse cloud generally keeps conditions settled and clear.",
        "all_of": (
            {"field": "season", "op": "eq", "value": "winter"},
            {"field": "pressure_hpa", "op": "gte", "value": 1019},
            {"field": "cloud_cover_pct", "op": "lte", "value": 22},
            {"field": "humidity_pct", "op": "lte", "value": 58},
        ),
    },
    {
        "condition": "cloudy",
        "weight": 1.18,
        "reason": "Widespread cloud cover with moist air but usable visibility usually indicates a cloudy shield rather than fog.",
        "all_of": (
            {"field": "cloud_cover_pct", "op": "gte", "value": 82},
            {"field": "humidity_pct", "op": "gte", "value": 68},
            {"field": "visibility_km", "op": "gte", "value": 5},
        ),
    },
    {
        "condition": "cloudy",
        "weight": 1.12,
        "reason": "Moist but weakly forced air masses often remain broadly cloudy without organized precipitation.",
        "all_of": (
            {"field": "cloud_cover_pct", "op": "gte", "value": 68},
            {"field": "pressure_hpa", "op": "between", "value": [1006, 1016]},
            {"field": "wind_kph", "op": "lte", "value": 24},
        ),
    },
    {
        "condition": "cloudy",
        "weight": 1.14,
        "reason": "Monsoon humidity and broad cloud decks often sustain overcast conditions even without peak rainfall.",
        "all_of": (
            {"field": "season", "op": "eq", "value": "monsoon"},
            {"field": "cloud_cover_pct", "op": "gte", "value": 70},
            {"field": "humidity_pct", "op": "gte", "value": 75},
        ),
    },
    {
        "condition": "windy",
        "weight": 1.34,
        "reason": "Strong wind plus a tight low-pressure gradient is a direct windy-weather signal.",
        "all_of": (
            {"field": "wind_kph", "op": "gte", "value": 38},
            {"field": "pressure_hpa", "op": "lte", "value": 1004},
        ),
    },
    {
        "condition": "windy",
        "weight": 1.22,
        "reason": "Dry fast-moving air masses often show up as windy but relatively clear advection regimes.",
        "all_of": (
            {"field": "wind_kph", "op": "gte", "value": 34},
            {"field": "humidity_pct", "op": "lte", "value": 45},
            {"field": "visibility_km", "op": "gte", "value": 8},
        ),
    },
    {
        "condition": "clear",
        "weight": 0.78,
        "reason": "Extensive overcast strongly suppresses clear-sky likelihood.",
        "all_of": ({"field": "cloud_cover_pct", "op": "gte", "value": 82},),
    },
    {
        "condition": "fog",
        "weight": 0.72,
        "reason": "Stronger winds usually disrupt the shallow stable layer needed for fog.",
        "all_of": ({"field": "wind_kph", "op": "gte", "value": 22},),
    },
    {
        "condition": "drizzle",
        "weight": 0.78,
        "reason": "Strong winds tend to break up shallow drizzle-producing cloud layers.",
        "all_of": ({"field": "wind_kph", "op": "gte", "value": 30},),
    },
    {
        "condition": "thunderstorm",
        "weight": 0.82,
        "reason": "Strong high pressure and a rising barometer usually suppress convective storm development.",
        "all_of": (
            {"field": "pressure_hpa", "op": "gte", "value": 1017},
            {"field": "pressure_trend", "op": "eq", "value": "rising"},
        ),
    },
    {
        "condition": "rain",
        "weight": 0.74,
        "reason": "Hot dry sunny air significantly reduces near-term rain odds.",
        "all_of": (
            {"field": "humidity_pct", "op": "lte", "value": 38},
            {"field": "cloud_cover_pct", "op": "lte", "value": 25},
            {"field": "uv_index", "op": "gte", "value": 8},
        ),
    },
    {
        "condition": "rain",
        "weight": 0.8,
        "reason": "Very low cloud cover and no recent rain suppress wet-weather continuation.",
        "all_of": (
            {"field": "cloud_cover_pct", "op": "lte", "value": 18},
            {"field": "recent_rain_mm", "op": "lte", "value": 0.5},
        ),
    },
    {
        "condition": "fog",
        "weight": 0.78,
        "reason": "Daytime heating and decent visibility work against persistent fog.",
        "all_of": (
            {"field": "hour_24", "op": "between", "value": [10, 16]},
            {"field": "temperature_c", "op": "gte", "value": 24},
            {"field": "visibility_km", "op": "gte", "value": 8},
        ),
    },
    {
        "condition": "cloudy",
        "weight": 0.84,
        "reason": "Dry air with high pressure and little cloud cover suppresses broad cloudy outcomes.",
        "all_of": (
            {"field": "pressure_hpa", "op": "gte", "value": 1016},
            {"field": "humidity_pct", "op": "lte", "value": 42},
            {"field": "cloud_cover_pct", "op": "lte", "value": 25},
        ),
    },
    {
        "condition": "clear",
        "weight": 0.74,
        "reason": "Deep monsoon moisture and heavy overcast sharply reduce clear-sky likelihood.",
        "all_of": (
            {"field": "season", "op": "eq", "value": "monsoon"},
            {"field": "humidity_pct", "op": "gte", "value": 84},
            {"field": "cloud_cover_pct", "op": "gte", "value": 78},
        ),
    },
    {
        "condition": "thunderstorm",
        "weight": 0.84,
        "reason": "Cool stable low-UV conditions usually suppress thunderstorm formation.",
        "all_of": (
            {"field": "temperature_c", "op": "lte", "value": 22},
            {"field": "uv_index", "op": "lte", "value": 3},
            {"field": "pressure_trend", "op": "eq", "value": "rising"},
        ),
    },
    {
        "condition": "drizzle",
        "weight": 0.82,
        "reason": "Intense daytime heating and mixing generally work against persistent drizzle.",
        "all_of": (
            {"field": "temperature_c", "op": "gte", "value": 32},
            {"field": "wind_kph", "op": "gte", "value": 22},
        ),
    },
    {
        "condition": "clear",
        "weight": 0.82,
        "reason": "Low visibility itself is a signal against truly clear conditions.",
        "all_of": ({"field": "visibility_km", "op": "lte", "value": 4},),
    },
)


def export_knowledge_base() -> dict[str, Any]:
    return {
        "base_priors": BASE_PRIORS,
        "seasonal_multipliers": SEASONAL_MULTIPLIERS,
        "terrain_multipliers": TERRAIN_MULTIPLIERS,
        "climate_zone_multipliers": CLIMATE_ZONE_MULTIPLIERS,
        "monthly_multipliers": MONTHLY_MULTIPLIERS,
        "risk_mode_alert_weights": RISK_MODE_ALERT_WEIGHTS,
        "risk_mode_thresholds": RISK_MODE_THRESHOLDS,
        "location_climate_hints": CLIMATE_ZONE_BY_LOCATION_HINT,
        "expert_rules": list(EXPERT_RULES),
    }


def infer_climate_zone(location: str, location_hints: dict[str, str] | None = None) -> str:
    hints = location_hints or CLIMATE_ZONE_BY_LOCATION_HINT
    token = location.strip().lower()
    if token in hints:
        return hints[token]
    for hint, zone in hints.items():
        if hint in token:
            return zone
    return "continental"


def _rule_context(obs: dict[str, Any]) -> dict[str, Any]:
    hour = int(obs["hour_24"])
    return {
        **obs,
        "dew_point_spread_c": round(obs["temperature_c"] - obs["dew_point_c"], 3),
        "is_night": 1 if hour <= 5 or hour >= 20 else 0,
        "is_morning": 1 if 5 <= hour <= 9 else 0,
        "is_afternoon": 1 if 12 <= hour <= 17 else 0,
        "is_evening": 1 if 18 <= hour <= 22 else 0,
    }


def _matches_clause(actual: Any, op: str, expected: Any) -> bool:
    if op == "gte":
        return actual >= expected
    if op == "gt":
        return actual > expected
    if op == "lte":
        return actual <= expected
    if op == "lt":
        return actual < expected
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if op == "between":
        low, high = expected
        return low <= actual <= high
    raise ValueError(f"Unsupported rule operator: {op}")


def _rule_matches(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    all_of = rule.get("all_of", [])
    any_of = rule.get("any_of", [])
    for clause in all_of:
        if not _matches_clause(context[clause["field"]], clause["op"], clause["value"]):
            return False
    if any_of:
        return any(_matches_clause(context[clause["field"]], clause["op"], clause["value"]) for clause in any_of)
    return True


def expert_rules(obs: dict[str, Any], rule_specs: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None) -> list[RuleEffect]:
    context = _rule_context(obs)
    rules = rule_specs or EXPERT_RULES
    effects: list[RuleEffect] = []
    for rule in rules:
        if _rule_matches(rule, context):
            effects.append(RuleEffect(rule["condition"], float(rule["weight"]), str(rule["reason"])))
    return effects

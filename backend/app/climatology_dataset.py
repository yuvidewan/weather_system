from __future__ import annotations

import math
import random
from typing import Any


CITY_CLIMATE_PROFILE = {
    "new delhi": {"zone": "continental", "humidity": 56, "rain_bias": 0.02, "thunder_bias": 0.04},
    "mumbai": {"zone": "humid_tropical", "humidity": 79, "rain_bias": 0.2, "thunder_bias": 0.08},
    "bengaluru": {"zone": "plateau", "humidity": 67, "rain_bias": 0.1, "thunder_bias": 0.12},
    "chennai": {"zone": "humid_tropical", "humidity": 75, "rain_bias": 0.16, "thunder_bias": 0.09},
    "hyderabad": {"zone": "plateau", "humidity": 61, "rain_bias": 0.08, "thunder_bias": 0.1},
    "kolkata": {"zone": "humid_tropical", "humidity": 78, "rain_bias": 0.17, "thunder_bias": 0.1},
    "pune": {"zone": "plateau", "humidity": 64, "rain_bias": 0.07, "thunder_bias": 0.11},
    "ahmedabad": {"zone": "arid", "humidity": 46, "rain_bias": -0.05, "thunder_bias": 0.03},
    "jaipur": {"zone": "arid", "humidity": 38, "rain_bias": -0.08, "thunder_bias": 0.02},
    "lucknow": {"zone": "continental", "humidity": 58, "rain_bias": 0.03, "thunder_bias": 0.05},
    "kanpur": {"zone": "continental", "humidity": 57, "rain_bias": 0.02, "thunder_bias": 0.05},
    "nagpur": {"zone": "continental", "humidity": 60, "rain_bias": 0.05, "thunder_bias": 0.09},
    "indore": {"zone": "plateau", "humidity": 56, "rain_bias": 0.02, "thunder_bias": 0.08},
    "bhopal": {"zone": "plateau", "humidity": 59, "rain_bias": 0.04, "thunder_bias": 0.08},
    "patna": {"zone": "continental", "humidity": 66, "rain_bias": 0.08, "thunder_bias": 0.07},
    "surat": {"zone": "humid_tropical", "humidity": 74, "rain_bias": 0.14, "thunder_bias": 0.08},
    "vadodara": {"zone": "continental", "humidity": 58, "rain_bias": 0.02, "thunder_bias": 0.05},
    "coimbatore": {"zone": "plateau", "humidity": 65, "rain_bias": 0.05, "thunder_bias": 0.09},
    "kochi": {"zone": "humid_tropical", "humidity": 82, "rain_bias": 0.23, "thunder_bias": 0.1},
    "goa": {"zone": "humid_tropical", "humidity": 81, "rain_bias": 0.24, "thunder_bias": 0.1},
    "shimla": {"zone": "highland", "humidity": 63, "rain_bias": 0.04, "thunder_bias": 0.02},
    "leh": {"zone": "highland", "humidity": 31, "rain_bias": -0.12, "thunder_bias": 0.01},
}

CONDITION_NAMES = ("clear", "cloudy", "rain", "drizzle", "thunderstorm", "fog", "windy")
YEARS = tuple(range(2006, 2026))
DAYS_PER_MONTH = 28


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _seasonal_rain_signal(month: int) -> float:
    monsoon_peak = math.exp(-((month - 7.5) ** 2) / 3.5)
    retreat_peak = math.exp(-((month - 10.0) ** 2) / 4.8)
    return 0.55 * monsoon_peak + 0.22 * retreat_peak


def _winter_fog_signal(month: int) -> float:
    return math.exp(-((month - 1.8) ** 2) / 3.0)


def _summer_clear_signal(month: int) -> float:
    return math.exp(-((month - 5.0) ** 2) / 5.0)


def _condition_distribution(city_bias: dict[str, float], month: int, day: int, rng: random.Random) -> dict[str, float]:
    rain_base = 0.18 + _seasonal_rain_signal(month) + city_bias["rain_bias"]
    thunder_base = 0.06 + 0.28 * _seasonal_rain_signal(month) + city_bias["thunder_bias"]
    drizzle_base = 0.07 + 0.22 * _seasonal_rain_signal(month) + max(0, city_bias["rain_bias"]) * 0.18
    fog_base = 0.06 + 0.2 * _winter_fog_signal(month)
    clear_base = 0.24 + 0.3 * _summer_clear_signal(month) - 0.22 * _seasonal_rain_signal(month)
    windy_base = 0.09 + 0.04 * math.sin((month / 12) * 2 * math.pi)
    cloudy_base = 0.18 + 0.16 * _seasonal_rain_signal(month)

    weekly_wave = 0.03 * math.sin(day / 7.0)
    noise = lambda spread: rng.uniform(-spread, spread)

    raw = {
        "clear": clear_base + weekly_wave + noise(0.03),
        "cloudy": cloudy_base + noise(0.025),
        "rain": rain_base + noise(0.035),
        "drizzle": drizzle_base + noise(0.02),
        "thunderstorm": thunder_base + noise(0.02),
        "fog": fog_base + noise(0.02),
        "windy": windy_base + noise(0.02),
    }
    clipped = {k: _clamp(v, 0.01, 0.9) for k, v in raw.items()}
    total = sum(clipped.values())
    return {k: clipped[k] / total for k in CONDITION_NAMES}


def _city_features(city_bias: dict[str, float], month: int, dist: dict[str, float], rng: random.Random) -> dict[str, float]:
    humidity = _clamp(city_bias["humidity"] + 24 * _seasonal_rain_signal(month) + rng.uniform(-8, 8), 18, 98)
    cloud = _clamp(34 + 56 * (dist["cloudy"] + dist["rain"] + dist["drizzle"]) + rng.uniform(-12, 12), 5, 100)
    pressure = _clamp(1013 - 20 * dist["rain"] - 25 * dist["thunderstorm"] + rng.uniform(-4, 4), 960, 1042)
    wind = _clamp(9 + 34 * dist["windy"] + 14 * dist["thunderstorm"] + rng.uniform(-4, 4), 0, 95)
    rain_mm = _clamp(32 * dist["rain"] + 15 * dist["drizzle"] + 18 * dist["thunderstorm"] + rng.uniform(0, 6), 0, 240)
    return {
        "avg_humidity_pct": round(humidity, 2),
        "avg_cloud_cover_pct": round(cloud, 2),
        "avg_pressure_hpa": round(pressure, 2),
        "avg_wind_kph": round(wind, 2),
        "avg_recent_rain_mm": round(rain_mm, 2),
    }


def build_dataset() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for city, profile in CITY_CLIMATE_PROFILE.items():
        for year in YEARS:
            for month in range(1, 13):
                month_rng = random.Random(f"{city}-{year}-{month}-climatology")
                weighted_dist = {k: 0.0 for k in CONDITION_NAMES}
                weighted_features = {
                    "avg_humidity_pct": 0.0,
                    "avg_cloud_cover_pct": 0.0,
                    "avg_pressure_hpa": 0.0,
                    "avg_wind_kph": 0.0,
                    "avg_recent_rain_mm": 0.0,
                }
                for day in range(1, DAYS_PER_MONTH + 1):
                    dist = _condition_distribution(profile, month, day, month_rng)
                    features = _city_features(profile, month, dist, month_rng)
                    for key in weighted_dist:
                        weighted_dist[key] += dist[key]
                    for key in weighted_features:
                        weighted_features[key] += features[key]

                records = DAYS_PER_MONTH
                rows.append(
                    {
                        "city": city,
                        "zone": profile["zone"],
                        "year": year,
                        "month": month,
                        "records": records,
                        "condition_distribution": {k: round(weighted_dist[k] / records, 4) for k in CONDITION_NAMES},
                        "feature_summary": {k: round(weighted_features[k] / records, 2) for k in weighted_features},
                    }
                )
    return rows


DATASET_ROWS = build_dataset()


def dataset_stats() -> dict[str, Any]:
    cities = sorted({row["city"] for row in DATASET_ROWS})
    zones = sorted({row["zone"] for row in DATASET_ROWS})
    return {
        "rows": len(DATASET_ROWS),
        "cities": len(cities),
        "climate_zones": len(zones),
        "year_range": [min(YEARS), max(YEARS)],
        "records_per_row": DAYS_PER_MONTH,
        "notes": "Synthetic multi-decade climatology used only for low-weight prior smoothing to reduce variance.",
    }


def _canonical_city(location: str) -> str:
    token = location.strip().lower()
    if token in CITY_CLIMATE_PROFILE:
        return token
    if token in {"delhi", "new delhi"}:
        return "new delhi"
    if token in {"bengaluru", "bangalore"}:
        return "bengaluru"
    return "new delhi"


def climatology_distribution(location: str, month: int) -> dict[str, Any]:
    city = _canonical_city(location)
    rows = [row for row in DATASET_ROWS if row["city"] == city and row["month"] == month]
    if not rows:
        rows = [row for row in DATASET_ROWS if row["month"] == month]

    sample_count = sum(row["records"] for row in rows)
    blended = {k: 0.0 for k in CONDITION_NAMES}
    for row in rows:
        weight = row["records"]
        for key, val in row["condition_distribution"].items():
            blended[key] += weight * val
    for key in blended:
        blended[key] = round(blended[key] / max(sample_count, 1), 4)

    return {
        "city": city,
        "month": month,
        "sample_count": sample_count,
        "distribution": blended,
    }

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


def fetch_live_weather(lat: float, lon: float) -> dict[str, Any]:
    """
    Optional live ingestion via Open-Meteo endpoint.
    Falls back to deterministic synthetic output if network is unavailable.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,cloud_cover"
    )
    timeout = float(os.getenv("LIVE_PROVIDER_TIMEOUT_SEC", "3.0"))
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            current = payload.get("current", {})
            return {
                "provider": "open-meteo",
                "source": "live",
                "temperature_c": float(current.get("temperature_2m", 28.0)),
                "humidity_pct": float(current.get("relative_humidity_2m", 60.0)),
                "pressure_hpa": float(current.get("surface_pressure", 1008.0)),
                "wind_kph": float(current.get("wind_speed_10m", 12.0)),
                "cloud_cover_pct": float(current.get("cloud_cover", 45.0)),
            }
    except (URLError, TimeoutError, OSError, ValueError):
        base = (abs(lat) + abs(lon)) % 1
        return {
            "provider": "synthetic-fallback",
            "source": "fallback",
            "temperature_c": round(24 + 10 * base, 1),
            "humidity_pct": round(45 + 35 * base, 1),
            "pressure_hpa": round(1002 + 10 * (1 - base), 1),
            "wind_kph": round(10 + 15 * base, 1),
            "cloud_cover_pct": round(35 + 40 * base, 1),
        }


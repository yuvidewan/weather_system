from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

from .storage import read_live_cache, write_live_cache


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime) -> str:
    return ts.isoformat()


def _cache_key(lat: float, lon: float, provider: str) -> str:
    return f"{provider}:{round(lat, 3)}:{round(lon, 3)}"


def _open_meteo(lat: float, lon: float, timeout: float) -> dict[str, Any]:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,cloud_cover"
    )
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


def _wttr(lat: float, lon: float, timeout: float) -> dict[str, Any]:
    location_token = quote(f"{lat},{lon}")
    url = f"https://wttr.in/{location_token}?format=j1"
    with urlopen(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
        current = (payload.get("current_condition") or [{}])[0]
        return {
            "provider": "wttr.in",
            "source": "live",
            "temperature_c": float(current.get("temp_C", 28.0)),
            "humidity_pct": float(current.get("humidity", 60.0)),
            "pressure_hpa": float(current.get("pressure", 1008.0)),
            "wind_kph": float(current.get("windspeedKmph", 12.0)),
            "cloud_cover_pct": float(current.get("cloudcover", 45.0)),
        }


def _synthetic(lat: float, lon: float) -> dict[str, Any]:
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


def fetch_live_weather(lat: float, lon: float, provider_preference: str = "auto") -> dict[str, Any]:
    """
    Provider abstraction with persistent cache and fallback chain.
    provider_preference: auto | open-meteo | wttr
    """
    timeout = float(os.getenv("LIVE_PROVIDER_TIMEOUT_SEC", "3.0"))
    cache_ttl_sec = int(os.getenv("LIVE_CACHE_TTL_SEC", "600"))

    providers = {
        "open-meteo": _open_meteo,
        "wttr": _wttr,
    }

    if provider_preference in providers:
        order = [provider_preference]
    else:
        order = ["open-meteo", "wttr"]

    now = _now_utc()
    for provider_name in order:
        cache_key = _cache_key(lat, lon, provider_name)
        cached = read_live_cache(cache_key, _iso(now))
        if cached is not None:
            payload = dict(cached)
            payload["source"] = "cache"
            return payload

        provider_fn = providers[provider_name]
        try:
            payload = provider_fn(lat, lon, timeout)
            expires = now + timedelta(seconds=cache_ttl_sec)
            write_live_cache(cache_key, payload, _iso(expires), _iso(now))
            return payload
        except (URLError, TimeoutError, OSError, ValueError, KeyError):
            continue

    return _synthetic(lat, lon)

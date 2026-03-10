from __future__ import annotations

from typing import Any

from .knowledge_base import export_knowledge_base
from .storage import get_active_kb_version


_REQUIRED_KEYS = {
    "base_priors",
    "seasonal_multipliers",
    "terrain_multipliers",
    "climate_zone_multipliers",
    "monthly_multipliers",
    "risk_mode_alert_weights",
    "risk_mode_thresholds",
}


def resolve_runtime_knowledge() -> dict[str, Any]:
    default_payload = export_knowledge_base()
    active = get_active_kb_version()
    if not active:
        return default_payload

    payload = active.get("payload", {})
    if not isinstance(payload, dict):
        return default_payload
    if not _REQUIRED_KEYS.issubset(set(payload.keys())):
        return default_payload
    merged_payload = dict(default_payload)
    merged_payload.update(payload)
    return merged_payload

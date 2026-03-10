from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .storage import write_notification_log


ALERT_RANK = {
    "low": 0,
    "moderate": 1,
    "high": 2,
    "severe": 3,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def should_trigger(subscription: dict[str, Any], forecast: dict[str, Any]) -> bool:
    if not subscription.get("enabled", 1):
        return False
    if subscription["location"] != "*" and subscription["location"].lower() != forecast["location"].lower():
        return False
    if subscription["risk_mode"] != "*" and subscription["risk_mode"] != forecast["risk_mode"]:
        return False
    if float(forecast["rain_probability"]) < float(subscription["min_rain_probability"]):
        return False
    min_rank = ALERT_RANK.get(subscription["min_alert_level"], 0)
    got_rank = ALERT_RANK.get(forecast["alert_level"], 0)
    return got_rank >= min_rank


def _deliver_webhook(target: str, payload: dict[str, Any]) -> tuple[str, str]:
    req = Request(
        target,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=3.0) as response:
            status = response.status
        if 200 <= status < 300:
            return "delivered", f"webhook status={status}"
        return "failed", f"webhook status={status}"
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return "failed", f"webhook error={exc}"


def deliver_notification(subscription: dict[str, Any], forecast: dict[str, Any]) -> None:
    payload = {
        "subscription": {
            "id": subscription["id"],
            "name": subscription["name"],
            "channel": subscription["channel"],
            "target": subscription["target"],
        },
        "forecast": forecast,
        "timestamp_utc": _now_utc(),
    }
    channel = subscription["channel"]

    if channel == "webhook":
        status, message = _deliver_webhook(subscription["target"], payload)
    elif channel == "email":
        status, message = "queued", "email channel is simulated in this environment"
    elif channel == "sms":
        status, message = "queued", "sms channel is simulated in this environment"
    else:
        status, message = "queued", "log channel recorded"

    write_notification_log(
        payload["timestamp_utc"],
        int(subscription["id"]),
        status,
        message,
        payload,
    )

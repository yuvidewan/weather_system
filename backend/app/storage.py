from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parents[1] / "weather_expert.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS forecast_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                location TEXT NOT NULL,
                risk_mode TEXT NOT NULL,
                predicted_condition TEXT NOT NULL,
                rain_probability REAL NOT NULL,
                alert_level TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS forecast_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                location TEXT NOT NULL,
                risk_mode TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                predicted_rain_probability REAL NOT NULL,
                actual_condition TEXT NOT NULL,
                actual_rain_mm REAL NOT NULL,
                outcome_rain INTEGER NOT NULL,
                absolute_error REAL NOT NULL,
                brier_score REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_utc TEXT NOT NULL,
                name TEXT NOT NULL,
                channel TEXT NOT NULL,
                target TEXT NOT NULL,
                location TEXT NOT NULL,
                risk_mode TEXT NOT NULL,
                min_rain_probability REAL NOT NULL,
                min_alert_level TEXT NOT NULL,
                enabled INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                subscription_id INTEGER NOT NULL,
                delivery_status TEXT NOT NULL,
                message TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_base_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_name TEXT NOT NULL,
                created_utc TEXT NOT NULL,
                created_by TEXT NOT NULL,
                notes TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                is_active INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS live_weather_cache (
                cache_key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                expires_utc TEXT NOT NULL,
                updated_utc TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def write_forecast(item: dict[str, Any]) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO forecast_history (
                timestamp_utc, location, risk_mode, predicted_condition, rain_probability, alert_level
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                item["timestamp_utc"],
                item["location"],
                item["risk_mode"],
                item["predicted_condition"],
                item["rain_probability"],
                item["alert_level"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def write_audit(timestamp_utc: str, actor: str, action: str, detail: str) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO audit_log (timestamp_utc, actor, action, detail) VALUES (?, ?, ?, ?)",
            (timestamp_utc, actor, action, detail),
        )
        conn.commit()
    finally:
        conn.close()


def read_history(
    *,
    limit: int = 100,
    location: str | None = None,
    risk_mode: str | None = None,
    alert_level: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if location:
        clauses.append("location = ?")
        params.append(location)
    if risk_mode:
        clauses.append("risk_mode = ?")
        params.append(risk_mode)
    if alert_level:
        clauses.append("alert_level = ?")
        params.append(alert_level)
    if date_from:
        clauses.append("timestamp_utc >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("timestamp_utc <= ?")
        params.append(date_to)

    params.append(limit)
    where_sql = " AND ".join(clauses)

    conn = _connect()
    try:
        rows = conn.execute(
            f"""
            SELECT timestamp_utc, location, risk_mode, predicted_condition, rain_probability, alert_level
            FROM forecast_history
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def read_history_analytics(
    *,
    location: str | None = None,
    risk_mode: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    clauses = ["1=1"]
    params: list[Any] = []
    if location:
        clauses.append("location = ?")
        params.append(location)
    if risk_mode:
        clauses.append("risk_mode = ?")
        params.append(risk_mode)
    if date_from:
        clauses.append("timestamp_utc >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("timestamp_utc <= ?")
        params.append(date_to)
    where_sql = " AND ".join(clauses)

    conn = _connect()
    try:
        summary = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total_forecasts,
                AVG(rain_probability) AS avg_rain_probability,
                AVG(CASE WHEN alert_level IN ('high', 'severe') THEN 1.0 ELSE 0.0 END) AS high_alert_ratio
            FROM forecast_history
            WHERE {where_sql}
            """,
            params,
        ).fetchone()

        timeline = conn.execute(
            f"""
            SELECT
                substr(timestamp_utc, 1, 10) AS date,
                COUNT(*) AS count,
                ROUND(AVG(rain_probability), 4) AS avg_rain_probability,
                SUM(CASE WHEN alert_level = 'severe' THEN 1 ELSE 0 END) AS severe_count
            FROM forecast_history
            WHERE {where_sql}
            GROUP BY substr(timestamp_utc, 1, 10)
            ORDER BY date DESC
            LIMIT 30
            """,
            params,
        ).fetchall()

        by_location = conn.execute(
            f"""
            SELECT
                location,
                COUNT(*) AS count,
                ROUND(AVG(rain_probability), 4) AS avg_rain_probability,
                SUM(CASE WHEN alert_level IN ('high', 'severe') THEN 1 ELSE 0 END) AS high_alert_count
            FROM forecast_history
            WHERE {where_sql}
            GROUP BY location
            ORDER BY count DESC
            LIMIT 20
            """,
            params,
        ).fetchall()

        return {
            "summary": {
                "total_forecasts": int(summary["total_forecasts"] or 0),
                "avg_rain_probability": round(float(summary["avg_rain_probability"] or 0.0), 4),
                "high_alert_ratio": round(float(summary["high_alert_ratio"] or 0.0), 4),
            },
            "timeline": [dict(row) for row in timeline],
            "by_location": [dict(row) for row in by_location],
        }
    finally:
        conn.close()


def write_outcome(item: dict[str, Any]) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO forecast_outcomes (
                timestamp_utc,
                location,
                risk_mode,
                horizon_hours,
                predicted_rain_probability,
                actual_condition,
                actual_rain_mm,
                outcome_rain,
                absolute_error,
                brier_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["timestamp_utc"],
                item["location"],
                item["risk_mode"],
                item["horizon_hours"],
                item["predicted_rain_probability"],
                item["actual_condition"],
                item["actual_rain_mm"],
                item["outcome_rain"],
                item["absolute_error"],
                item["brier_score"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def read_calibration(location: str | None = None) -> dict[str, Any]:
    clauses = ["1=1"]
    params: list[Any] = []
    if location:
        clauses.append("location = ?")
        params.append(location)
    where_sql = " AND ".join(clauses)

    conn = _connect()
    try:
        overall = conn.execute(
            f"""
            SELECT
                COUNT(*) AS sample_count,
                ROUND(AVG(brier_score), 4) AS avg_brier_score,
                ROUND(AVG(absolute_error), 4) AS avg_absolute_error
            FROM forecast_outcomes
            WHERE {where_sql}
            """,
            params,
        ).fetchone()

        bins = conn.execute(
            f"""
            SELECT
                CAST(predicted_rain_probability * 10 AS INTEGER) AS prob_bin,
                COUNT(*) AS count,
                ROUND(AVG(outcome_rain), 4) AS observed_rain_frequency,
                ROUND(AVG(predicted_rain_probability), 4) AS avg_predicted
            FROM forecast_outcomes
            WHERE {where_sql}
            GROUP BY CAST(predicted_rain_probability * 10 AS INTEGER)
            ORDER BY prob_bin
            """,
            params,
        ).fetchall()

        by_location = conn.execute(
            """
            SELECT
                location,
                COUNT(*) AS sample_count,
                ROUND(AVG(brier_score), 4) AS avg_brier_score
            FROM forecast_outcomes
            GROUP BY location
            ORDER BY sample_count DESC
            LIMIT 20
            """
        ).fetchall()

        return {
            "overall": {
                "sample_count": int(overall["sample_count"] or 0),
                "avg_brier_score": float(overall["avg_brier_score"] or 0.0),
                "avg_absolute_error": float(overall["avg_absolute_error"] or 0.0),
            },
            "reliability_bins": [dict(row) for row in bins],
            "by_location": [dict(row) for row in by_location],
        }
    finally:
        conn.close()


def create_alert_subscription(item: dict[str, Any]) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO alert_subscriptions (
                created_utc,
                name,
                channel,
                target,
                location,
                risk_mode,
                min_rain_probability,
                min_alert_level,
                enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["created_utc"],
                item["name"],
                item["channel"],
                item["target"],
                item["location"],
                item["risk_mode"],
                item["min_rain_probability"],
                item["min_alert_level"],
                1 if item.get("enabled", True) else 0,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def read_alert_subscriptions(enabled_only: bool = True) -> list[dict[str, Any]]:
    conn = _connect()
    try:
        where_sql = "WHERE enabled = 1" if enabled_only else ""
        rows = conn.execute(
            f"""
            SELECT id, created_utc, name, channel, target, location, risk_mode, min_rain_probability, min_alert_level, enabled
            FROM alert_subscriptions
            {where_sql}
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def set_alert_subscription_enabled(subscription_id: int, enabled: bool) -> None:
    conn = _connect()
    try:
        conn.execute(
            "UPDATE alert_subscriptions SET enabled = ? WHERE id = ?",
            (1 if enabled else 0, subscription_id),
        )
        conn.commit()
    finally:
        conn.close()


def write_notification_log(
    timestamp_utc: str,
    subscription_id: int,
    delivery_status: str,
    message: str,
    payload: dict[str, Any],
) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO notification_log (
                timestamp_utc,
                subscription_id,
                delivery_status,
                message,
                payload_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp_utc, subscription_id, delivery_status, message, json.dumps(payload)),
        )
        conn.commit()
    finally:
        conn.close()


def read_notification_log(limit: int = 100) -> list[dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT timestamp_utc, subscription_id, delivery_status, message, payload_json
            FROM notification_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            out.append(item)
        return out
    finally:
        conn.close()


def create_kb_version(
    *,
    version_name: str,
    created_utc: str,
    created_by: str,
    notes: str,
    payload: dict[str, Any],
    is_active: bool,
) -> int:
    conn = _connect()
    try:
        if is_active:
            conn.execute("UPDATE knowledge_base_versions SET is_active = 0")
        cur = conn.execute(
            """
            INSERT INTO knowledge_base_versions (
                version_name,
                created_utc,
                created_by,
                notes,
                payload_json,
                is_active
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (version_name, created_utc, created_by, notes, json.dumps(payload), 1 if is_active else 0),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_kb_versions() -> list[dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, version_name, created_utc, created_by, notes, is_active
            FROM knowledge_base_versions
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def activate_kb_version(version_id: int) -> bool:
    conn = _connect()
    try:
        target = conn.execute("SELECT id FROM knowledge_base_versions WHERE id = ?", (version_id,)).fetchone()
        if not target:
            return False
        conn.execute("UPDATE knowledge_base_versions SET is_active = 0")
        conn.execute("UPDATE knowledge_base_versions SET is_active = 1 WHERE id = ?", (version_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_active_kb_version() -> dict[str, Any] | None:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, version_name, created_utc, created_by, notes, payload_json
            FROM knowledge_base_versions
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        return item
    finally:
        conn.close()


def read_kb_version(version_id: int) -> dict[str, Any] | None:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, version_name, created_utc, created_by, notes, payload_json, is_active
            FROM knowledge_base_versions
            WHERE id = ?
            """,
            (version_id,),
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        return item
    finally:
        conn.close()


def read_live_cache(cache_key: str, now_utc: str) -> dict[str, Any] | None:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT payload_json
            FROM live_weather_cache
            WHERE cache_key = ? AND expires_utc > ?
            """,
            (cache_key, now_utc),
        ).fetchone()
        if not row:
            return None
        return json.loads(row["payload_json"])
    finally:
        conn.close()


def write_live_cache(cache_key: str, payload: dict[str, Any], expires_utc: str, updated_utc: str) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO live_weather_cache (cache_key, payload_json, expires_utc, updated_utc)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key)
            DO UPDATE SET payload_json = excluded.payload_json, expires_utc = excluded.expires_utc, updated_utc = excluded.updated_utc
            """,
            (cache_key, json.dumps(payload), expires_utc, updated_utc),
        )
        conn.commit()
    finally:
        conn.close()

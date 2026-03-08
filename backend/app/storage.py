from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parents[1] / "weather_expert.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
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
        conn.commit()
    finally:
        conn.close()


def write_forecast(item: dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO audit_log (timestamp_utc, actor, action, detail) VALUES (?, ?, ?, ?)",
            (timestamp_utc, actor, action, detail),
        )
        conn.commit()
    finally:
        conn.close()


def read_history(limit: int = 100) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT timestamp_utc, location, risk_mode, predicted_condition, rain_probability, alert_level
            FROM forecast_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


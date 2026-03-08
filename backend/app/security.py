from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


ALLOWED_KEYS = {k.strip() for k in os.getenv("API_KEYS", "dev-admin-key,dev-analyst-key").split(",") if k.strip()}
ROLE_BY_KEY = {
    "dev-admin-key": "admin",
    "dev-analyst-key": "analyst",
}


def authorize(x_api_key: str = Header(default=""), x_role: str = Header(default="analyst")) -> str:
    if x_api_key not in ALLOWED_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    expected_role = ROLE_BY_KEY.get(x_api_key, "analyst")
    if x_role not in {"admin", "analyst", "viewer"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported role")
    if expected_role == "admin":
        return x_role
    if x_role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges for admin role")
    return x_role


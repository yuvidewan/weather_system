from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ConditionName = Literal["clear", "cloudy", "rain", "drizzle", "thunderstorm", "fog", "windy"]


class WeatherObservation(BaseModel):
    temperature_c: float = Field(..., ge=-50, le=60, description="Current temperature in Celsius")
    humidity_pct: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    pressure_hpa: float = Field(..., ge=870, le=1100, description="Sea-level pressure in hPa")
    wind_kph: float = Field(..., ge=0, le=220, description="Wind speed in kilometers per hour")
    cloud_cover_pct: float = Field(..., ge=0, le=100, description="Cloud cover percentage")
    dew_point_c: float = Field(..., ge=-60, le=40, description="Dew point in Celsius")
    recent_rain_mm: float = Field(0, ge=0, le=500, description="Rainfall in the last 6 hours")
    uv_index: float = Field(3, ge=0, le=15, description="UV index")
    visibility_km: float = Field(10, ge=0.1, le=60, description="Visibility in kilometers")
    month: int = Field(..., ge=1, le=12)
    hour_24: int = Field(..., ge=0, le=23)
    season: Literal["winter", "spring", "summer", "monsoon", "autumn"]
    terrain: Literal["coastal", "plains", "urban", "mountain", "forest", "desert"]
    pressure_trend: Literal["rising", "steady", "falling"] = "steady"


class InferenceRequest(BaseModel):
    location: str = Field("Unknown", max_length=80)
    observation: WeatherObservation
    horizon_hours: int = Field(6, ge=1, le=24, description="Prediction horizon in hours")


class ConditionProbability(BaseModel):
    condition: ConditionName
    probability: float = Field(..., ge=0, le=1)


class FactorImpact(BaseModel):
    factor: str
    impact: float
    direction: Literal["increases", "decreases"]


class InferenceResponse(BaseModel):
    location: str
    horizon_hours: int
    predicted_condition: ConditionName
    condition_probabilities: list[ConditionProbability]
    rain_probability: float = Field(..., ge=0, le=1)
    expected_rainfall_mm: float = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0, le=1)
    alert_level: Literal["low", "moderate", "high", "severe"]
    expert_recommendations: list[str]
    key_factors: list[FactorImpact]
    explanation: str


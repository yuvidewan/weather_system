from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ConditionName = Literal["clear", "cloudy", "rain", "drizzle", "thunderstorm", "fog", "windy"]
RiskMode = Literal["general", "agriculture", "travel", "events", "logistics"]
DataSourceName = Literal["manual", "station", "satellite", "radar", "model"]


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
    source_confidence: dict[DataSourceName, float] = Field(
        default_factory=lambda: {"manual": 0.8, "station": 0.85, "satellite": 0.82, "radar": 0.86, "model": 0.78}
    )


class InferenceRequest(BaseModel):
    location: str = Field("Unknown", max_length=80)
    observation: WeatherObservation
    horizon_hours: int = Field(6, ge=1, le=24, description="Prediction horizon in hours")
    risk_mode: RiskMode = "general"
    custom_thresholds: dict[str, float] = Field(default_factory=dict)


class ConditionProbability(BaseModel):
    condition: ConditionName
    probability: float = Field(..., ge=0, le=1)


class FactorImpact(BaseModel):
    factor: str
    impact: float
    direction: Literal["increases", "decreases"]


class ScenarioPoint(BaseModel):
    label: Literal["best_case", "expected_case", "worst_case"]
    rain_probability: float = Field(..., ge=0, le=1)
    expected_rainfall_mm: float = Field(..., ge=0)


class HorizonForecast(BaseModel):
    horizon_hours: int
    predicted_condition: ConditionName
    rain_probability: float = Field(..., ge=0, le=1)
    expected_rainfall_mm: float = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0, le=1)


class EventProbabilities(BaseModel):
    rain_onset_within_3h: float = Field(..., ge=0, le=1)
    storm_onset_within_6h: float = Field(..., ge=0, le=1)
    heavy_rain_within_12h: float = Field(..., ge=0, le=1)


class RainIntensityBands(BaseModel):
    light: float = Field(..., ge=0, le=1)
    moderate: float = Field(..., ge=0, le=1)
    heavy: float = Field(..., ge=0, le=1)
    extreme: float = Field(..., ge=0, le=1)


class RuleTrace(BaseModel):
    condition: ConditionName
    reason: str
    weight: float


class CounterfactualItem(BaseModel):
    change: str
    impact_on_rain_probability: float


class DataQuality(BaseModel):
    sensor_reliability: float = Field(..., ge=0, le=1)
    imputed_fields: list[str]
    uncertainty_penalty: float = Field(..., ge=0, le=1)


class InferenceResponse(BaseModel):
    location: str
    risk_mode: RiskMode
    horizon_hours: int
    predicted_condition: ConditionName
    condition_probabilities: list[ConditionProbability]
    rain_probability: float = Field(..., ge=0, le=1)
    expected_rainfall_mm: float = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0, le=1)
    alert_level: Literal["low", "moderate", "high", "severe"]
    expert_recommendations: list[str]
    key_factors: list[FactorImpact]
    feature_attributions: list[FactorImpact]
    rule_trace: list[RuleTrace]
    counterfactuals: list[CounterfactualItem]
    scenarios: list[ScenarioPoint]
    horizons: list[HorizonForecast]
    event_probabilities: EventProbabilities
    intensity_bands: RainIntensityBands
    data_quality: DataQuality
    explanation: str


class MultiLocationRequest(BaseModel):
    locations: list[str] = Field(..., min_length=1, max_length=10)
    observation: WeatherObservation
    horizon_hours: int = Field(6, ge=1, le=24)
    risk_mode: RiskMode = "general"


class MultiLocationItem(BaseModel):
    location: str
    predicted_condition: ConditionName
    rain_probability: float = Field(..., ge=0, le=1)
    alert_level: Literal["low", "moderate", "high", "severe"]


class MultiLocationResponse(BaseModel):
    count: int
    items: list[MultiLocationItem]

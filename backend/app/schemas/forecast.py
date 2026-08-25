from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional, List, Dict, Any


class ForecastBase(BaseModel):
    product_id: int
    store_id: int
    forecast_date: date
    predicted_units: float
    lower_bound: float
    upper_bound: float
    model_used: str = "ensemble"
    mape: Optional[float] = None
    rmse: Optional[float] = None


class ForecastCreate(ForecastBase):
    pass


class ForecastResponse(ForecastBase):
    id: int
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForecastPredictionItem(BaseModel):
    week_index: int
    forecast_date: str
    week_end_date: str
    predicted_units: float
    lower_bound: float
    upper_bound: float
    confidence_level: Any
    is_cold_start: bool = False
    model_used: str
    product_id: int
    store_id: int


class ForecastPredictionResponse(BaseModel):
    product_id: int
    store_id: int
    horizon_weeks: int
    model_type: str
    predictions: List[ForecastPredictionItem]


class ForecastTrainRequest(BaseModel):
    product_id: int
    store_id: int
    model_type: str = "ensemble"  # prophet, xgboost, ensemble
    version: str = "1.0"


class ForecastTrainResponse(BaseModel):
    status: str
    product_id: int
    store_id: int
    model_type: str
    version: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    artifact_path: Optional[str] = None
    is_cold_start: Optional[bool] = False
    message: Optional[str] = None


class ForecastEvaluateResponse(BaseModel):
    product_id: int
    store_id: int
    is_cold_start: bool
    status: Optional[str] = None
    message: Optional[str] = None
    ensemble_metrics: Optional[Dict[str, float]] = None
    prophet_metrics: Optional[Dict[str, float]] = None
    xgboost_metrics: Optional[Dict[str, float]] = None
    prophet_weight: Optional[float] = None
    xgboost_weight: Optional[float] = None
    mape: Optional[float] = None
    rmse: Optional[float] = None


class ForecastRetrainAllResponse(BaseModel):
    status: str
    frequency: str
    total_pairs: int
    success_count: int
    cold_start_count: int
    error_count: int
    forecast_results_created: int
    timestamp: str

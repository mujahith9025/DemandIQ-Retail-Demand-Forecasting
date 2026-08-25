from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AlertBase(BaseModel):
    type: str  # spike, drop, stockout
    severity: str  # critical, warning, info
    product_id: Optional[int] = None
    store_id: Optional[int] = None
    message: str
    status: str = "new"  # new, acknowledged, dismissed


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    type: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = None


class AlertPatchRequest(BaseModel):
    status: str = Field(..., pattern="^(new|acknowledged|dismissed)$")


class AlertResponse(AlertBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertConfigSchema(BaseModel):
    z_score_threshold: float = Field(2.5, ge=1.0, le=10.0)
    critical_z_threshold: float = Field(4.0, ge=2.0, le=15.0)
    isolation_forest_contamination: float = Field(0.05, ge=0.01, le=0.25)
    high_risk_doc_days: float = Field(7.0, ge=1.0, le=30.0)
    medium_risk_doc_days: float = Field(14.0, ge=2.0, le=60.0)
    lookback_window_days: int = Field(28, ge=7, le=120)


class AlertScanResponse(BaseModel):
    status: str
    scan_date: str
    sku_store_pairs_scanned: int
    zscore_anomalies_detected: int
    isolation_forest_anomalies_detected: int
    stockout_risks_detected: int
    new_alerts_created: int
    alerts_deduplicated_or_updated: int
    timestamp: str

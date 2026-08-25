from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date


class KPIOverview(BaseModel):
    total_products: int
    active_stores: int
    forecast_accuracy_pct: float
    stockout_risk_count: int
    overstock_risk_count: int
    projected_revenue_30d: float


class DemandTrendItem(BaseModel):
    date: str
    historical_sales: Optional[float] = None
    predicted_demand: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ReportSummaryResponse(BaseModel):
    generated_at: str
    kpis: KPIOverview
    trends: List[DemandTrendItem]
    top_demanded_skus: List[Dict[str, Any]]

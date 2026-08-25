from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DashboardKPIResponse(BaseModel):
    store_id: Optional[int] = None
    projected_revenue_30d: float
    revenue_growth_pct: float
    overall_accuracy_pct: float
    accuracy_change_pct: float
    total_active_products: int
    total_stores: int
    stockout_risk_count: int
    overstock_risk_count: int
    urgent_reorder_count: int
    generated_at: str


class ReportItemResponse(BaseModel):
    id: int
    title: str
    report_type: str
    format: str
    status: str
    created_at: str
    summary_metrics: Optional[Dict[str, Any]] = None

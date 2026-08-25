from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SimulatePromoRequest(BaseModel):
    product_id: Optional[int] = None
    category: Optional[str] = None
    discount_pct: float = Field(..., ge=0.0, le=100.0, description="Discount percentage (e.g. 20 for 20% off)")
    promo_duration_days: int = Field(default=14, ge=1, le=90, description="Duration in days")
    store_id: Optional[int] = None


class SimulationDayPoint(BaseModel):
    day_index: int
    date: str
    baseline_units: float
    simulated_units: float
    uplift_pct: float
    baseline_revenue: float
    simulated_revenue: float


class SimulatePromoResponse(BaseModel):
    product_id: Optional[int] = None
    category: Optional[str] = None
    discount_pct: float
    promo_duration_days: int
    estimated_elasticity: float
    total_baseline_units: float
    total_simulated_units: float
    total_unit_uplift: float
    total_unit_uplift_pct: float
    total_baseline_revenue: float
    total_simulated_revenue: float
    total_revenue_impact: float
    curve: List[SimulationDayPoint]

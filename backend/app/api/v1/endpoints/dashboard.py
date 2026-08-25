from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_store_access
from app.models.user import User
from app.schemas.dashboard import DashboardKPIResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/kpis",
    response_model=DashboardKPIResponse,
    summary="Get Aggregated Dashboard KPI Metrics",
    description="Returns top-line metrics including projected revenue, forecast accuracy, active products, and stockout risk counters.",
)
def get_dashboard_kpis(
    store_id: Optional[int] = Query(None, description="Optional Store ID filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_store = verify_store_access(store_id, current_user)
    service = DashboardService(db)
    return service.get_kpis(store_id=target_store)

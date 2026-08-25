from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_store_access
from app.models.user import User
from app.schemas.dashboard import ReportItemResponse
from app.schemas.common import PaginatedResponse
from app.services.reporting_service import ReportingService

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[ReportItemResponse],
    summary="List Saved Reports",
    description="Retrieve paginated list of generated business and forecasting reports.",
)
def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportingService(db)
    total, items = service.list_reports(limit=limit, offset=offset)

    formatted = [
        ReportItemResponse(
            id=r.id,
            title=r.title,
            report_type=r.report_type,
            format=r.format,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            summary_metrics=r.summary_metrics,
        )
        for r in items
    ]

    return PaginatedResponse[ReportItemResponse](
        total=total,
        limit=limit,
        offset=offset,
        items=formatted,
    )


@router.post(
    "/export",
    summary="Export Downloadable Report (CSV or PDF)",
    description="Generates dynamic report stream in CSV or PDF format.",
)
def export_report(
    report_type: str = Query("demand_summary", alias="type", description="demand_summary | accuracy_evaluation | inventory_health"),
    format_type: str = Query("csv", alias="format", description="csv | pdf"),
    store_id: Optional[int] = Query(None, description="Optional store filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_store = verify_store_access(store_id, current_user)
    service = ReportingService(db)
    filename, media_type, content = service.export_report(
        report_type=report_type,
        format_type=format_type,
        store_id=target_store,
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return Response(
        content=content,
        media_type=media_type,
        headers=headers,
    )

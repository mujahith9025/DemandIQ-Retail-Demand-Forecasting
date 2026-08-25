from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_store_access
from app.models.user import User
from app.models.alert import Alert
from app.schemas.alert import (
    AlertResponse,
    AlertPatchRequest,
    AlertCreate,
    AlertConfigSchema,
    AlertScanResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.anomaly_detection_service import AnomalyDetectionService, AlertConfig

router = APIRouter()

# In-memory mutable configuration (persists through process runtime)
_GLOBAL_ALERT_CONFIG = AlertConfig()


@router.get(
    "/config",
    response_model=AlertConfigSchema,
    summary="Get Anomaly Alert Configuration",
    description="Returns current z-score, Isolation Forest, and days-of-cover risk thresholds.",
)
def get_alert_config(
    current_user: User = Depends(get_current_user),
):
    return AlertConfigSchema(
        z_score_threshold=_GLOBAL_ALERT_CONFIG.z_score_threshold,
        critical_z_threshold=_GLOBAL_ALERT_CONFIG.critical_z_threshold,
        isolation_forest_contamination=_GLOBAL_ALERT_CONFIG.isolation_forest_contamination,
        high_risk_doc_days=_GLOBAL_ALERT_CONFIG.high_risk_doc_days,
        medium_risk_doc_days=_GLOBAL_ALERT_CONFIG.medium_risk_doc_days,
        lookback_window_days=_GLOBAL_ALERT_CONFIG.lookback_window_days,
    )


@router.post(
    "/config",
    response_model=AlertConfigSchema,
    summary="Update Anomaly Alert Configuration",
    description="Updates alerting thresholds for statistical z-scores and stockout risk classification.",
)
def update_alert_config(
    config_in: AlertConfigSchema,
    current_user: User = Depends(get_current_user),
):
    _GLOBAL_ALERT_CONFIG.z_score_threshold = config_in.z_score_threshold
    _GLOBAL_ALERT_CONFIG.critical_z_threshold = config_in.critical_z_threshold
    _GLOBAL_ALERT_CONFIG.isolation_forest_contamination = config_in.isolation_forest_contamination
    _GLOBAL_ALERT_CONFIG.high_risk_doc_days = config_in.high_risk_doc_days
    _GLOBAL_ALERT_CONFIG.medium_risk_doc_days = config_in.medium_risk_doc_days
    _GLOBAL_ALERT_CONFIG.lookback_window_days = config_in.lookback_window_days
    return config_in


@router.post(
    "/scan",
    response_model=AlertScanResponse,
    summary="Trigger Immediate Anomaly & Stockout Risk Scan",
    description="Executes a full anomaly detection scan across all active SKUs and stores.",
)
def trigger_anomaly_scan(
    target_date: Optional[date] = Query(None, description="Target date to scan for demand shocks (default yesterday)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AnomalyDetectionService(db, config=_GLOBAL_ALERT_CONFIG)
    results = service.run_full_anomaly_scan(target_date=target_date)
    return AlertScanResponse(**results)


@router.get(
    "/",
    response_model=PaginatedResponse[AlertResponse],
    summary="Filterable Paginated Alerts List",
    description="Retrieve alerts filtered by severity (critical, warning, info) and status (new, acknowledged, dismissed).",
)
def get_alerts(
    severity: Optional[str] = Query(None, description="critical | warning | info"),
    status_filter: Optional[str] = Query(None, alias="status", description="new | acknowledged | dismissed"),
    store_id: Optional[int] = Query(None, description="Store ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_store = verify_store_access(store_id, current_user)
    query = db.query(Alert)

    if severity:
        query = query.filter(Alert.severity == severity.lower())
    if status_filter:
        query = query.filter(Alert.status == status_filter.lower())
    if target_store:
        query = query.filter((Alert.store_id == target_store) | (Alert.store_id.is_(None)))

    total = query.count()
    items = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()

    return PaginatedResponse[AlertResponse](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.patch(
    "/{id}",
    response_model=AlertResponse,
    summary="Update Alert Status",
    description="Update alert status to acknowledged or dismissed.",
)
def update_alert_status(
    id: int = Path(..., description="Alert ID"),
    patch_in: AlertPatchRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {id} not found.",
        )

    if alert.store_id:
        verify_store_access(alert.store_id, current_user)

    alert.status = patch_in.status
    db.commit()
    db.refresh(alert)
    return alert


@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Alert Record",
)
def create_alert(
    alert_in: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if alert_in.store_id:
        verify_store_access(alert_in.store_id, current_user)

    alert = Alert(**alert_in.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

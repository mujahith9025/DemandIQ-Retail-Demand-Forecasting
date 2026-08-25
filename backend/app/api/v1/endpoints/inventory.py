from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_store_access
from app.models.user import User
from app.schemas.inventory import (
    InventoryResponse,
    ReorderRecommendationItem,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.inventory_service import InventoryService
from app.services.inventory_optimization_service import InventoryOptimizationService

router = APIRouter()


@router.get(
    "/recommendations",
    response_model=PaginatedResponse[ReorderRecommendationItem],
    summary="Get Statistical Inventory Reorder Recommendations",
    description="Returns calculated reorder recommendations with statistical safety stock, dynamic ROP, suggested order quantities, and Days-of-Cover risk classification.",
)
def get_reorder_recommendations(
    store_id: Optional[int] = Query(None, description="Filter by Store ID"),
    service_level: float = Query(0.95, ge=0.50, le=0.999, description="Target service level probability (e.g. 0.95 for 95%)"),
    high_risk_days: float = Query(7.0, ge=1.0, le=30.0, description="Days-of-cover threshold for High/Critical risk"),
    medium_risk_days: float = Query(14.0, ge=2.0, le=60.0, description="Days-of-cover threshold for Medium/Warning risk"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_store = verify_store_access(store_id, current_user)
    opt_service = InventoryOptimizationService(db)
    total, items = opt_service.get_recommendations(
        store_id=target_store,
        service_level=service_level,
        high_threshold_days=high_risk_days,
        medium_threshold_days=medium_risk_days,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse[ReorderRecommendationItem](
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.post(
    "/purchase-order",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Purchase Order Record",
    description="Creates a new purchase order from a reorder recommendation.",
)
def create_purchase_order(
    order_in: PurchaseOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_store_access(order_in.store_id, current_user)
    service = InventoryService(db)
    try:
        po = service.create_purchase_order(order_in=order_in, user_id=current_user.id)
        return po
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/",
    response_model=List[InventoryResponse],
    summary="Get Inventory Level Records",
)
def list_inventory(
    product_id: Optional[int] = Query(None),
    store_id: Optional[int] = Query(None),
    below_reorder_point: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_store = verify_store_access(store_id, current_user)
    service = InventoryService(db)
    return service.get_inventory_records(
        product_id=product_id,
        store_id=target_store,
        below_reorder_point=below_reorder_point,
    )

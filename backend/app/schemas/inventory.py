from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional, List


class InventoryBase(BaseModel):
    product_id: int
    store_id: int
    current_stock: int = 0
    reorder_point: int = 20
    safety_stock: int = 10


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    safety_stock: Optional[int] = None


class InventoryResponse(InventoryBase):
    id: int
    last_updated: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReorderRecommendationItem(BaseModel):
    product_id: int
    sku_code: str
    product_name: str
    category: str
    store_id: int
    current_stock: int
    reorder_point: int
    safety_stock: int
    lead_time_days: int
    suggested_order_qty: int
    unit_cost: float
    estimated_order_cost: float
    risk_level: str  # CRITICAL, WARNING, OK
    days_of_supply_remaining: float


class PurchaseOrderCreate(BaseModel):
    product_id: int
    store_id: int
    order_quantity: int = Field(..., gt=0)
    supplier_name: Optional[str] = "Default Supplier"
    expected_delivery_date: Optional[date] = None


class PurchaseOrderResponse(BaseModel):
    id: int
    product_id: int
    store_id: int
    order_quantity: int
    unit_cost: float
    total_cost: float
    status: str
    supplier_name: str
    expected_delivery_date: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

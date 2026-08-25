from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ProductBase(BaseModel):
    sku_code: str
    name: str
    category: str
    subcategory: Optional[str] = None
    unit_price: float
    unit_cost: float
    lead_time_days: int = 7


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku_code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    unit_price: Optional[float] = None
    unit_cost: Optional[float] = None
    lead_time_days: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

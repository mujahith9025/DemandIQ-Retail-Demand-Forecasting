from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


class SalesBase(BaseModel):
    product_id: int
    store_id: int
    date: date
    units_sold: int
    revenue: float
    promotion_id: Optional[int] = None


class SalesCreate(SalesBase):
    pass


class SalesResponse(SalesBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

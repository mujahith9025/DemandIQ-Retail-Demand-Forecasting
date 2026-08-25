from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


class PromotionBase(BaseModel):
    name: str
    discount_pct: float
    start_date: date
    end_date: date
    product_id: Optional[int] = None
    category: Optional[str] = None


class PromotionCreate(PromotionBase):
    pass


class PromotionResponse(PromotionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

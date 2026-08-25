from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class StoreBase(BaseModel):
    name: str
    location: str
    city: str
    region: str
    timezone: str = "UTC"


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    timezone: Optional[str] = None


class StoreResponse(StoreBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

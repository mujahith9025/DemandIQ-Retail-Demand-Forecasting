from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


class APIErrorResponse(BaseModel):
    detail: str = Field(description="Human-readable explanation of error")
    error_code: str = Field(default="INTERNAL_ERROR", description="Machine-readable error identifier")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int = Field(description="Total count of matching records")
    limit: int = Field(description="Number of records returned per page")
    offset: int = Field(description="Pagination starting offset")
    items: List[T] = Field(description="List of records for the requested page")

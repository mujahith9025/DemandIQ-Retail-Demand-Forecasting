from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RowValidationError(BaseModel):
    row_number: int = Field(description="1-based row index in CSV file")
    column: Optional[str] = Field(default=None, description="Affected column name if applicable")
    issue: str = Field(description="Clear explanation of the validation failure")
    raw_value: Optional[str] = Field(default=None, description="Offending raw string value in file")


class DataUploadErrorResponse(BaseModel):
    status: str = "validation_error"
    message: str = "CSV validation failed. No data was inserted into the database."
    error_count: int
    errors: List[RowValidationError]


class DataUploadSuccessResponse(BaseModel):
    status: str = "success"
    message: str = "Sales data validated and bulk-inserted successfully."
    total_rows: int
    inserted_rows: int
    date_range: Optional[Dict[str, str]] = None
    background_job_triggered: bool = True

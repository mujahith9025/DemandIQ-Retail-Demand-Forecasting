from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.data_ingestion import (
    DataUploadSuccessResponse,
    DataUploadErrorResponse,
)
from app.services.ingestion_service import SalesDataIngestionService
from app.services.aggregation_service import run_weekly_aggregation_background_task

router = APIRouter()


@router.post(
    "/upload",
    response_model=DataUploadSuccessResponse,
    responses={
        422: {"model": DataUploadErrorResponse, "description": "CSV Validation Errors"},
        400: {"model": DataUploadErrorResponse, "description": "Bad Request"},
    },
    summary="Upload Sales History CSV",
    description="Accepts sales history CSV files with columns: date, sku_code, store_id, units_sold, revenue. Performs strict validation, atomic bulk insert, and triggers background aggregation.",
)
async def upload_sales_csv(
    file: UploadFile = File(..., description="Sales CSV file to ingest"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    if not file.filename or not (file.filename.endswith(".csv") or file.filename.endswith(".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid CSV format (.csv extension).",
        )

    file_bytes = await file.read()
    if not file_bytes:
        return JSONResponse(
            status_code=422,
            content={
                "status": "validation_error",
                "message": "Uploaded file is completely empty.",
                "error_count": 1,
                "errors": [
                    {
                        "row_number": 1,
                        "column": None,
                        "issue": "Empty file provided.",
                        "raw_value": None,
                    }
                ],
            },
        )

    service = SalesDataIngestionService(db)
    is_valid, result = service.process_csv(file_bytes)

    if not is_valid:
        return JSONResponse(
            status_code=422,
            content=result.model_dump(),
        )

    # Queue background task to re-aggregate weekly sales summaries
    background_tasks.add_task(run_weekly_aggregation_background_task)

    return result


@router.post(
    "/aggregate/weekly",
    summary="Manually Trigger Weekly Sales Aggregation",
    description="Re-aggregates all daily sales into weekly summaries.",
)
def trigger_weekly_aggregation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    background_tasks.add_task(run_weekly_aggregation_background_task)
    return {
        "status": "queued",
        "message": "Weekly sales aggregation job has been scheduled in the background.",
    }

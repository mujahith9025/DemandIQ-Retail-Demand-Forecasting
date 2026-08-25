from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import Optional, List, Dict, Any
from datetime import date

from app.core.database import get_db
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.inventory import Inventory
from app.models.alert import Alert
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
    description="Accepts sales history CSV files with columns: date, sku_code, store_id, units_sold, revenue. Performs strict validation, atomic bulk upsert, and triggers background aggregation.",
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


@router.get(
    "/overview",
    summary="Get Database Dataset Overview & Table Counts",
    description="Returns aggregate counts and summary statistics for all database entities.",
)
def get_dataset_overview(db: Session = Depends(get_db)):
    sales_stats = db.query(
        func.count(Sales.id).label("total_sales_rows"),
        func.sum(Sales.units_sold).label("total_units"),
        func.sum(Sales.revenue).label("total_revenue"),
        func.min(Sales.date).label("min_date"),
        func.max(Sales.date).label("max_date"),
    ).first()

    return {
        "tables": {
            "sales": {
                "count": sales_stats.total_sales_rows or 0,
                "total_units_sold": int(sales_stats.total_units or 0),
                "total_revenue_inr": round(float(sales_stats.total_revenue or 0.0), 2),
                "start_date": str(sales_stats.min_date) if sales_stats.min_date else None,
                "end_date": str(sales_stats.max_date) if sales_stats.max_date else None,
            },
            "products": {
                "count": db.query(Product).count(),
            },
            "stores": {
                "count": db.query(Store).count(),
            },
            "inventories": {
                "count": db.query(Inventory).count(),
            },
            "alerts": {
                "count": db.query(Alert).count(),
            }
        }
    }


@router.get(
    "/sales",
    summary="Explore Sales History Dataset with Filtering & Pagination",
    description="Browse all sales records stored in the database.",
)
def explore_sales_dataset(
    store_id: Optional[int] = Query(None, description="Filter by Store ID"),
    sku_code: Optional[str] = Query(None, description="Filter by SKU Code"),
    start_date: Optional[date] = Query(None, description="Filter by Start Date"),
    end_date: Optional[date] = Query(None, description="Filter by End Date"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("date", description="Field to sort by (date, units_sold, revenue)"),
    order: str = Query("desc", description="Sort order (asc, desc)"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Sales.id,
            Sales.date,
            Product.sku_code,
            Product.name.label("product_name"),
            Product.category,
            Product.unit_price,
            Sales.store_id,
            Store.name.label("store_name"),
            Sales.units_sold,
            Sales.revenue,
        )
        .join(Product, Sales.product_id == Product.id)
        .join(Store, Sales.store_id == Store.id)
    )

    if store_id:
        query = query.filter(Sales.store_id == store_id)
    if sku_code:
        query = query.filter(Product.sku_code.ilike(f"%{sku_code}%"))
    if start_date:
        query = query.filter(Sales.date >= start_date)
    if end_date:
        query = query.filter(Sales.date <= end_date)

    total_count = query.count()

    # Calculate summary metrics for the filtered subset
    stats = (
        query.with_entities(
            func.sum(Sales.units_sold).label("filtered_units"),
            func.sum(Sales.revenue).label("filtered_revenue"),
        ).first()
    )

    # Sorting
    sort_column = Sales.date
    if sort_by == "units_sold":
        sort_column = Sales.units_sold
    elif sort_by == "revenue":
        sort_column = Sales.revenue

    if order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    records = query.offset(offset).limit(limit).all()

    items = [
        {
            "id": r.id,
            "date": str(r.date),
            "sku_code": r.sku_code,
            "product_name": r.product_name,
            "category": r.category,
            "unit_price": r.unit_price,
            "store_id": r.store_id,
            "store_name": r.store_name,
            "units_sold": r.units_sold,
            "revenue": round(r.revenue, 2),
        }
        for r in records
    ]

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "summary": {
            "total_units": int(stats.filtered_units or 0) if stats else 0,
            "total_revenue_inr": round(float(stats.filtered_revenue or 0.0), 2) if stats else 0.0,
        },
        "items": items,
    }


@router.get(
    "/catalog",
    summary="Explore Product Catalog & Inventory Levels",
    description="Returns all products with current stock and metrics.",
)
def explore_catalog_dataset(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    stores = db.query(Store).all()
    inventories = db.query(Inventory).all()

    return {
        "products": [
            {
                "id": p.id,
                "sku_code": p.sku_code,
                "name": p.name,
                "category": p.category,
                "subcategory": p.subcategory,
                "unit_price": p.unit_price,
                "unit_cost": p.unit_cost,
                "lead_time_days": p.lead_time_days,
            }
            for p in products
        ],
        "stores": [
            {
                "id": s.id,
                "name": s.name,
                "location": s.location,
                "city": s.city,
                "region": s.region,
                "timezone": s.timezone,
            }
            for s in stores
        ],
        "inventories": [
            {
                "id": inv.id,
                "product_id": inv.product_id,
                "store_id": inv.store_id,
                "current_stock": inv.current_stock,
                "reorder_point": inv.reorder_point,
                "safety_stock": inv.safety_stock,
            }
            for inv in inventories
        ]
    }


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

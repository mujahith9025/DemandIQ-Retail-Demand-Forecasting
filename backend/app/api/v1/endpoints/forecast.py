from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, verify_store_access
from app.models.user import User
from app.schemas.forecast import (
    ForecastResponse,
    ForecastPredictionResponse,
    ForecastPredictionItem,
    ForecastTrainRequest,
    ForecastTrainResponse,
    ForecastEvaluateResponse,
    ForecastRetrainAllResponse,
)
from app.services.forecasting_service import ForecastingService

router = APIRouter()


@router.get(
    "/accuracy",
    response_model=ForecastEvaluateResponse,
    summary="Get Forecast Accuracy Metrics (MAPE & RMSE)",
    description="Returns MAPE, RMSE, and model weighting history on validation sets.",
)
def get_forecast_accuracy(
    product_id: int = Query(..., description="Target Product ID"),
    store_id: int = Query(..., description="Target Store ID"),
    validation_weeks: int = Query(4, ge=1, le=26),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_store_id = verify_store_access(store_id, current_user)
    service = ForecastingService(db)
    try:
        res = service.evaluate(
            product_id=product_id,
            store_id=target_store_id or store_id,
            validation_weeks=validation_weeks,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/retrain",
    response_model=ForecastRetrainAllResponse,
    summary="Trigger Manual / Batch Retraining (Admin & Planner Only)",
    description="Retrains all active SKU-store combinations and persists results to the database.",
)
def retrain_forecasts(
    horizon_weeks: int = Query(4, ge=1, le=12),
    frequency: str = Query("manual", description="manual | daily | weekly | monthly"),
    current_user: User = Depends(require_roles(["admin", "planner"])),
    db: Session = Depends(get_db),
):
    service = ForecastingService(db)
    return service.retrain_all_active_skus(
        horizon_weeks=horizon_weeks,
        frequency=frequency,
    )


@router.get(
    "/{product_id}",
    response_model=ForecastPredictionResponse,
    summary="Get Forecast Series with Confidence Bands",
    description="Generates future demand predictions with confidence intervals for the given product and store.",
)
def get_product_forecast(
    product_id: int = Path(..., description="Target Product ID"),
    store_id: Optional[int] = Query(None, description="Target Store ID (defaults to assigned store for store managers)"),
    horizon_weeks: int = Query(4, ge=1, le=52, description="Horizon in weeks"),
    model_type: str = Query("ensemble", description="prophet | xgboost | ensemble"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    effective_store_id = verify_store_access(store_id, current_user) or store_id or 1
    service = ForecastingService(db)
    try:
        predictions = service.predict(
            product_id=product_id,
            store_id=effective_store_id,
            horizon_weeks=horizon_weeks,
            model_type=model_type,
        )
        return ForecastPredictionResponse(
            product_id=product_id,
            store_id=effective_store_id,
            horizon_weeks=horizon_weeks,
            model_type=model_type,
            predictions=predictions,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting error: {str(e)}",
        )


@router.post(
    "/train",
    response_model=ForecastTrainResponse,
    summary="Train Specific SKU-Store Model",
)
def train_specific_sku(
    req: ForecastTrainRequest,
    current_user: User = Depends(require_roles(["admin", "planner"])),
    db: Session = Depends(get_db),
):
    service = ForecastingService(db)
    try:
        return service.train(
            product_id=req.product_id,
            store_id=req.store_id,
            model_type=req.model_type,
            version=req.version,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/",
    response_model=List[ForecastResponse],
    summary="Query Historical Forecast Database Records",
)
def list_forecast_records(
    product_id: Optional[int] = Query(None),
    store_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_store = verify_store_access(store_id, current_user)
    service = ForecastingService(db)
    return service.get_forecasts(
        product_id=product_id,
        store_id=target_store,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

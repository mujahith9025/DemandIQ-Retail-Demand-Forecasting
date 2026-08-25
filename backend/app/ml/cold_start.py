import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product
from app.models.sales import Sales


def is_cold_start(sales_records: List[Any], min_history_days: int = 56) -> bool:
    """
    Check if an SKU-store series has less than 8 weeks (56 days) of sales history.
    """
    if not sales_records or len(sales_records) < 10:
        return True

    dates = [
        s.date if isinstance(s.date, date) else pd.to_datetime(s.date).date()
        for s in sales_records
    ]
    min_date = min(dates)
    max_date = max(dates)
    total_span_days = (max_date - min_date).days + 1

    return total_span_days < min_history_days


def get_category_average_daily_demand(
    db: Session,
    category: str,
    default_if_empty: float = 15.0,
) -> float:
    """
    Calculate average daily sales velocity across all products in the specified category.
    """
    result = (
        db.query(func.avg(Sales.units_sold))
        .join(Product, Sales.product_id == Product.id)
        .filter(Product.category == category)
        .scalar()
    )

    if result is not None and result > 0:
        return float(result)

    # Fallback to general product average
    general_avg = db.query(func.avg(Sales.units_sold)).scalar()
    if general_avg is not None and general_avg > 0:
        return float(general_avg)

    return default_if_empty


def generate_cold_start_forecast(
    category_avg_demand: float,
    horizon_days: int = 28,
    start_date: Optional[date] = None,
    product: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Generate naive category-level benchmark forecast for cold-start products.
    Flagged clearly as 'low' confidence.
    """
    if start_date is None:
        start_date = date.today()

    base_demand = max(1.0, float(category_avg_demand))
    predictions = []

    for i in range(horizon_days):
        cur_date = start_date + timedelta(days=i)
        cur_dt = pd.to_datetime(cur_date)
        dow = cur_dt.dayofweek

        # Weekend uplift heuristic for retail (e.g. +15% on Sat/Sun)
        day_factor = 1.15 if dow in [5, 6] else 0.95
        point_pred = round(base_demand * day_factor, 2)

        # Wide uncertainty band (+/- 40%) for cold start
        lower_bound = round(max(0.0, point_pred * 0.60), 2)
        upper_bound = round(point_pred * 1.40, 2)

        predictions.append(
            {
                "date": cur_date.isoformat(),
                "predicted_units": point_pred,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "confidence_level": "low",
                "is_cold_start": True,
                "model_used": "category_average_fallback",
            }
        )

    return predictions

import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


def build_daily_time_series(
    sales_records: List[Any],
    product: Any,
    promotions: List[Any],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    """
    Construct a contiguous daily time-series dataframe from sparse sales records.
    Missing dates are imputed with 0 units sold.
    """
    if not sales_records:
        return pd.DataFrame()

    # Convert sales records to list of dicts
    data = []
    for s in sales_records:
        d = s.date if isinstance(s.date, date) else datetime.strptime(str(s.date), "%Y-%m-%d").date()
        data.append(
            {
                "date": pd.to_datetime(d),
                "units_sold": float(s.units_sold),
                "revenue": float(s.revenue),
                "store_id": int(s.store_id),
                "product_id": int(s.product_id),
            }
        )

    df_sales = pd.DataFrame(data)
    df_sales = df_sales.sort_values("date").drop_duplicates(subset=["date"])

    min_d = df_sales["date"].min() if start_date is None else pd.to_datetime(start_date)
    max_d = df_sales["date"].max() if end_date is None else pd.to_datetime(end_date)

    full_date_range = pd.date_range(start=min_d, end=max_d, freq="D", name="date")
    df = pd.DataFrame(index=full_date_range).reset_index()

    df = df.merge(df_sales, on="date", how="left")
    df["units_sold"] = df["units_sold"].fillna(0.0)
    df["revenue"] = df["revenue"].fillna(0.0)
    df["product_id"] = product.id
    if len(df_sales) > 0 and "store_id" in df_sales.columns:
        df["store_id"] = df["store_id"].ffill().bfill().fillna(1)

    # Product features
    df["unit_price"] = float(product.unit_price)
    df["unit_cost"] = float(product.unit_cost)
    df["margin"] = float(product.unit_price - product.unit_cost)
    df["lead_time_days"] = int(product.lead_time_days)
    df["category"] = str(product.category)
    df["subcategory"] = str(product.subcategory or "General")

    # Promotion Active indicator
    df["is_promotion_active"] = 0
    if promotions:
        for p in promotions:
            p_start = pd.to_datetime(p.start_date)
            p_end = pd.to_datetime(p.end_date)
            mask = (df["date"] >= p_start) & (df["date"] <= p_end)
            df.loc[mask, "is_promotion_active"] = 1

    return df


def engineer_features(
    df: pd.DataFrame,
    lags: List[int] = [1, 7, 14, 28],
    windows: List[int] = [7, 14, 28],
) -> pd.DataFrame:
    """
    Generate lag, rolling window, calendar, and encoding features.
    """
    if df.empty:
        return df

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 1. Calendar Features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_month_start"] = df["date"].dt.is_month_start.astype(int)
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)

    # Cyclical encoding for day of week and month
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)

    # 2. Lag Features
    for lag in lags:
        df[f"units_sold_lag_{lag}"] = df["units_sold"].shift(lag)

    # 3. Rolling Window Statistics (shifted by 1 day to prevent data leakage)
    for window in windows:
        shifted = df["units_sold"].shift(1)
        df[f"units_sold_rolling_mean_{window}"] = shifted.rolling(window, min_periods=1).mean()
        df[f"units_sold_rolling_std_{window}"] = shifted.rolling(window, min_periods=1).std().fillna(0.0)
        df[f"units_sold_rolling_max_{window}"] = shifted.rolling(window, min_periods=1).max()
        df[f"units_sold_rolling_min_{window}"] = shifted.rolling(window, min_periods=1).min()

    # Fill remaining lag NaNs with backward fill then 0
    feature_cols = [c for c in df.columns if "lag" in c or "rolling" in c]
    for c in feature_cols:
        df[c] = df[c].bfill().fillna(0.0)

    return df


def get_feature_column_names() -> List[str]:
    """Return the canonical list of feature columns used by XGBoost."""
    return [
        "day_of_week",
        "day_of_month",
        "month",
        "week_of_year",
        "is_weekend",
        "is_month_start",
        "is_month_end",
        "dow_sin",
        "dow_cos",
        "month_sin",
        "month_cos",
        "is_promotion_active",
        "unit_price",
        "unit_cost",
        "margin",
        "lead_time_days",
        "units_sold_lag_1",
        "units_sold_lag_7",
        "units_sold_lag_14",
        "units_sold_lag_28",
        "units_sold_rolling_mean_7",
        "units_sold_rolling_std_7",
        "units_sold_rolling_max_7",
        "units_sold_rolling_min_7",
        "units_sold_rolling_mean_14",
        "units_sold_rolling_std_14",
        "units_sold_rolling_max_14",
        "units_sold_rolling_min_14",
        "units_sold_rolling_mean_28",
        "units_sold_rolling_std_28",
        "units_sold_rolling_max_28",
        "units_sold_rolling_min_28",
    ]

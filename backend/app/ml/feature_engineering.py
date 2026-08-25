import pandas as pd
import numpy as np
from typing import List, Dict, Any


def extract_calendar_features(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """Extract temporal features (day of week, month, day of year, weekend indicator)."""
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    df["day_of_week"] = df[date_column].dt.dayofweek
    df["day_of_month"] = df[date_column].dt.day
    df["month"] = df[date_column].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    return df


def create_lag_features(df: pd.DataFrame, target_column: str = "units_sold", lags: List[int] = [7, 14, 28]) -> pd.DataFrame:
    """Generate historical lag and rolling window features."""
    df = df.copy()
    for lag in lags:
        df[f"{target_column}_lag_{lag}"] = df[target_column].shift(lag)
    df[f"{target_column}_rolling_mean_7"] = df[target_column].shift(1).rolling(7).mean()
    df[f"{target_column}_rolling_mean_28"] = df[target_column].shift(1).rolling(28).mean()
    return df

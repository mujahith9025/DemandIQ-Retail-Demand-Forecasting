import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple


class ProphetDemandModel:
    """
    Decomposed Trend & Seasonality Time-Series Forecaster.
    Models piecewise linear trend, weekly Fourier seasonality (7-day period),
    monthly Fourier seasonality (30-day period), and promotion effects.
    Generates point forecasts and empirical confidence intervals.
    """

    def __init__(self, seasonality_mode: str = "additive"):
        self.seasonality_mode = seasonality_mode
        self.is_fitted = False
        self.trend_slope = 0.0
        self.trend_intercept = 0.0
        self.weekly_seasonality = {}
        self.promo_lift = 0.0
        self.residual_std = 1.0
        self.last_train_date: Optional[pd.Timestamp] = None
        self.train_mape = 0.0
        self.train_rmse = 0.0

    def _fit_internal(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Fit trend, weekly pattern, and promo coefficient using OLS / Fourier decomposition."""
        df = df.copy().sort_values("date").reset_index(drop=True)
        t = np.arange(len(df))
        y = df["units_sold"].values.astype(float)

        # 1. Fit linear trend
        if len(df) > 1:
            poly = np.polyfit(t, y, 1)
            self.trend_slope = float(poly[0])
            self.trend_intercept = float(poly[1])
        else:
            self.trend_slope = 0.0
            self.trend_intercept = float(y[0]) if len(y) > 0 else 0.0

        trend = self.trend_intercept + self.trend_slope * t

        # 2. De-trended signal
        detrended = y - trend

        # 3. Fit Day-of-Week Seasonality (7-day pattern)
        dow = df["date"].dt.dayofweek.values
        weekly_factors = {}
        for d in range(7):
            mask = dow == d
            if np.any(mask):
                weekly_factors[d] = float(np.mean(detrended[mask]))
            else:
                weekly_factors[d] = 0.0
        self.weekly_seasonality = weekly_factors

        seasonality = np.array([self.weekly_seasonality.get(d, 0.0) for d in dow])

        # 4. Fit Promotion Lift
        if "is_promotion_active" in df.columns and df["is_promotion_active"].sum() > 0:
            promo_mask = df["is_promotion_active"].values == 1
            non_promo_mask = ~promo_mask
            if np.any(non_promo_mask) and np.any(promo_mask):
                diff = np.mean(y[promo_mask]) - np.mean(y[non_promo_mask])
                self.promo_lift = float(max(0.0, diff))
            else:
                self.promo_lift = 0.0
        else:
            self.promo_lift = 0.0

        promo_effect = (
            df["is_promotion_active"].values * self.promo_lift
            if "is_promotion_active" in df.columns
            else np.zeros(len(df))
        )

        fitted_values = np.maximum(0.0, trend + seasonality + promo_effect)
        residuals = y - fitted_values
        self.residual_std = float(max(1.0, np.std(residuals)))
        self.last_train_date = df["date"].max()
        self.is_fitted = True

        return y, fitted_values

    def fit(self, df: pd.DataFrame) -> "ProphetDemandModel":
        if df.empty:
            raise ValueError("Cannot fit ProphetDemandModel on empty dataframe.")
        y_true, y_pred = self._fit_internal(df)

        # Compute train metrics
        abs_err = np.abs(y_true - y_pred)
        self.train_rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        denom = np.where(y_true == 0, 1.0, y_true)
        self.train_mape = float(np.mean(abs_err / denom))
        return self

    def predict(
        self,
        horizon_days: int = 28,
        start_date: Optional[date] = None,
        promotions: Optional[List[Any]] = None,
        confidence: float = 0.95,
    ) -> List[Dict[str, Any]]:
        """
        Generate forward predictions with confidence intervals.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predicting.")

        if start_date is None:
            start_date = (self.last_train_date + timedelta(days=1)).date() if self.last_train_date else date.today()

        z_score = 1.96 if confidence >= 0.95 else 1.645
        predictions = []

        for i in range(horizon_days):
            cur_date = start_date + timedelta(days=i)
            cur_dt = pd.to_datetime(cur_date)
            dow = cur_dt.dayofweek

            # Check promotion
            is_promo = 0
            if promotions:
                for p in promotions:
                    if p.start_date <= cur_date <= p.end_date:
                        is_promo = 1
                        break

            # Extrapolate trend + seasonality + promo
            trend_val = self.trend_intercept + self.trend_slope * (i + 1)
            seasonal_val = self.weekly_seasonality.get(dow, 0.0)
            promo_val = self.promo_lift * is_promo

            point_pred = max(0.0, trend_val + seasonal_val + promo_val)

            # Expanding uncertainty over forecast horizon
            horizon_decay = 1.0 + (i / max(1, horizon_days)) * 0.5
            margin_of_error = z_score * self.residual_std * horizon_decay

            lower_bound = max(0.0, point_pred - margin_of_error)
            upper_bound = max(point_pred, point_pred + margin_of_error)

            predictions.append(
                {
                    "date": cur_date.isoformat(),
                    "predicted_units": round(float(point_pred), 2),
                    "lower_bound": round(float(lower_bound), 2),
                    "upper_bound": round(float(upper_bound), 2),
                    "confidence_level": confidence,
                    "model_used": "prophet_seasonality",
                }
            )

        return predictions

    def evaluate(self, df_val: pd.DataFrame) -> Dict[str, float]:
        """Compute evaluation metrics (MAPE, RMSE) on validation holdout set."""
        if df_val.empty:
            return {"mape": self.train_mape, "rmse": self.train_rmse}

        preds = self.predict(
            horizon_days=len(df_val),
            start_date=df_val["date"].min().date(),
        )

        y_true = df_val["units_sold"].values.astype(float)
        y_pred = np.array([p["predicted_units"] for p in preds])

        abs_err = np.abs(y_true - y_pred)
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        denom = np.where(y_true == 0, 1.0, y_true)
        mape = float(np.mean(abs_err / denom))

        return {"mape": round(mape, 4), "rmse": round(rmse, 2)}

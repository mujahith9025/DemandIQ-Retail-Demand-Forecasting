from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import date

from app.ml.models.prophet_model import ProphetDemandModel
from app.ml.models.xgboost_model import XGBoostDemandModel


class EnsembleDemandModel:
    """
    Accuracy-Weighted Ensemble Forecaster.
    Blends Prophet (seasonality/trend) and XGBoost (autoregressive lag/feature regression)
    weighted inversely by their holdout validation MAPE.
    """

    def __init__(self):
        self.prophet_model = ProphetDemandModel()
        self.xgboost_model = XGBoostDemandModel()
        self.prophet_weight = 0.5
        self.xgboost_weight = 0.5
        self.prophet_metrics = {"mape": 0.1, "rmse": 5.0}
        self.xgboost_metrics = {"mape": 0.1, "rmse": 5.0}
        self.ensemble_metrics = {"mape": 0.08, "rmse": 4.5}
        self.is_fitted = False

    def fit(
        self,
        df_train: pd.DataFrame,
        df_val: Optional[pd.DataFrame] = None,
    ) -> "EnsembleDemandModel":
        # 1. Fit both models on training data
        self.prophet_model.fit(df_train)
        self.xgboost_model.fit(df_train)

        # 2. Compute validation metrics
        val_data = df_val if (df_val is not None and not df_val.empty) else df_train.tail(14)

        self.prophet_metrics = self.prophet_model.evaluate(val_data)
        self.xgboost_metrics = self.xgboost_model.evaluate(val_data)

        # 3. Calculate dynamic inverse-error weights
        eps = 1e-4
        inv_prophet = 1.0 / (max(0.01, self.prophet_metrics.get("mape", 0.1)) + eps)
        inv_xgboost = 1.0 / (max(0.01, self.xgboost_metrics.get("mape", 0.1)) + eps)

        total_inv = inv_prophet + inv_xgboost
        self.prophet_weight = float(round(inv_prophet / total_inv, 4))
        self.xgboost_weight = float(round(1.0 - self.prophet_weight, 4))

        # Overall ensemble estimated metrics
        self.ensemble_metrics = {
            "mape": round(
                self.prophet_weight * self.prophet_metrics.get("mape", 0.1)
                + self.xgboost_weight * self.xgboost_metrics.get("mape", 0.1),
                4,
            ),
            "rmse": round(
                self.prophet_weight * self.prophet_metrics.get("rmse", 5.0)
                + self.xgboost_weight * self.xgboost_metrics.get("rmse", 5.0),
                2,
            ),
        }

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon_days: int = 28,
        start_date: Optional[date] = None,
        promotions: Optional[List[Any]] = None,
        confidence: float = 0.95,
    ) -> List[Dict[str, Any]]:
        """Generate blended predictions."""
        if not self.is_fitted:
            raise RuntimeError("Ensemble model must be fitted before predicting.")

        prophet_preds = self.prophet_model.predict(
            horizon_days=horizon_days,
            start_date=start_date,
            promotions=promotions,
            confidence=confidence,
        )
        xgboost_preds = self.xgboost_model.predict(
            horizon_days=horizon_days,
            start_date=start_date,
            promotions=promotions,
            confidence=confidence,
        )

        blended = []
        for p_pred, x_pred in zip(prophet_preds, xgboost_preds):
            pred_val = (
                self.prophet_weight * p_pred["predicted_units"]
                + self.xgboost_weight * x_pred["predicted_units"]
            )
            low_val = (
                self.prophet_weight * p_pred["lower_bound"]
                + self.xgboost_weight * x_pred["lower_bound"]
            )
            up_val = (
                self.prophet_weight * p_pred["upper_bound"]
                + self.xgboost_weight * x_pred["upper_bound"]
            )

            # Ensure mathematical invariants: 0 <= lower <= pred <= upper
            pred_val = max(0.0, float(pred_val))
            low_val = max(0.0, min(pred_val, float(low_val)))
            up_val = max(pred_val, float(up_val))

            blended.append(
                {
                    "date": p_pred["date"],
                    "predicted_units": round(pred_val, 2),
                    "lower_bound": round(low_val, 2),
                    "upper_bound": round(up_val, 2),
                    "confidence_level": confidence,
                    "model_used": "accuracy_weighted_ensemble",
                    "ensemble_weights": {
                        "prophet": self.prophet_weight,
                        "xgboost": self.xgboost_weight,
                    },
                }
            )

        return blended

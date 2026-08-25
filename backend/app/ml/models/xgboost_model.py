import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
import xgboost as xgb

from app.ml.features import get_feature_column_names, engineer_features


class XGBoostDemandModel:
    """
    Gradient-boosted decision tree regression model for retail demand forecasting.
    Utilizes lag features, rolling window statistics, calendar signals, and promotion state.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.05,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            objective="reg:squarederror",
            n_jobs=1,
        )
        self.feature_columns = get_feature_column_names()
        self.is_fitted = False
        self.residual_std = 1.0
        self.last_train_date: Optional[pd.Timestamp] = None
        self.last_feature_state: Optional[pd.DataFrame] = None
        self.train_mape = 0.0
        self.train_rmse = 0.0

    def fit(self, df_features: pd.DataFrame) -> "XGBoostDemandModel":
        if df_features.empty or len(df_features) < 5:
            raise ValueError("Insufficient data points to fit XGBoostDemandModel (need >= 5).")

        df = df_features.copy().sort_values("date").reset_index(drop=True)
        available_features = [c for c in self.feature_columns if c in df.columns]

        X = df[available_features].values
        y = df["units_sold"].values.astype(float)

        self.model.fit(X, y)
        y_pred = np.maximum(0.0, self.model.predict(X))
        residuals = y - y_pred

        self.residual_std = float(max(1.0, np.std(residuals)))
        self.last_train_date = df["date"].max()
        self.last_feature_state = df.tail(35).copy()
        self.is_fitted = True

        abs_err = np.abs(y - y_pred)
        self.train_rmse = float(np.sqrt(np.mean(residuals ** 2)))
        denom = np.where(y == 0, 1.0, y)
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
        Iterative multi-step autoregressive forecasting.
        """
        if not self.is_fitted or self.last_feature_state is None:
            raise RuntimeError("Model must be fitted before predicting.")

        if start_date is None:
            start_date = (self.last_train_date + timedelta(days=1)).date() if self.last_train_date else date.today()

        available_features = [c for c in self.feature_columns if c in self.last_feature_state.columns]
        history = self.last_feature_state.copy()

        z_score = 1.96 if confidence >= 0.95 else 1.645
        predictions = []

        product_meta = {
            "unit_price": history["unit_price"].iloc[-1] if "unit_price" in history else 50.0,
            "unit_cost": history["unit_cost"].iloc[-1] if "unit_cost" in history else 25.0,
            "margin": history["margin"].iloc[-1] if "margin" in history else 25.0,
            "lead_time_days": history["lead_time_days"].iloc[-1] if "lead_time_days" in history else 7,
            "category": history["category"].iloc[-1] if "category" in history else "General",
            "subcategory": history["subcategory"].iloc[-1] if "subcategory" in history else "General",
            "store_id": history["store_id"].iloc[-1] if "store_id" in history else 1,
            "product_id": history["product_id"].iloc[-1] if "product_id" in history else 1,
        }

        for i in range(horizon_days):
            cur_date = start_date + timedelta(days=i)
            cur_dt = pd.to_datetime(cur_date)

            is_promo = 0
            if promotions:
                for p in promotions:
                    if p.start_date <= cur_date <= p.end_date:
                        is_promo = 1
                        break

            # Create new row
            new_row = {
                "date": cur_dt,
                "units_sold": 0.0,  # placeholder
                "revenue": 0.0,
                "is_promotion_active": is_promo,
                **product_meta,
            }

            temp_df = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)
            temp_df = engineer_features(temp_df)

            X_cur = temp_df[available_features].iloc[-1:].values
            point_pred = max(0.0, float(self.model.predict(X_cur)[0]))

            # Update historical record with predicted value for autoregressive next step
            temp_df.loc[temp_df.index[-1], "units_sold"] = point_pred
            temp_df.loc[temp_df.index[-1], "revenue"] = point_pred * product_meta["unit_price"]
            history = temp_df.tail(40).copy()

            horizon_decay = 1.0 + (i / max(1, horizon_days)) * 0.6
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
                    "model_used": "xgboost_regression",
                }
            )

        return predictions

    def evaluate(self, df_val: pd.DataFrame) -> Dict[str, float]:
        """Compute MAPE and RMSE on validation set."""
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

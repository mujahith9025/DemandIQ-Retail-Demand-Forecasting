import math
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.promotion import Promotion
from app.models.forecast import ForecastResult
from app.ml.features import build_daily_time_series, engineer_features
from app.ml.models.prophet_model import ProphetDemandModel
from app.ml.models.xgboost_model import XGBoostDemandModel
from app.ml.models.ensemble import EnsembleDemandModel
from app.ml.cold_start import (
    is_cold_start,
    get_category_average_daily_demand,
    generate_cold_start_forecast,
)
from app.ml.storage import ModelStorage


class ForecastingService:
    """
    Intelligent Retail Demand Forecasting Service.
    Supports Prophet (seasonality), XGBoost (lag/feature regression),
    accuracy-weighted Ensemble, cold-start fallback, and scheduled retraining.
    """

    def __init__(self, db: Session, storage: Optional[ModelStorage] = None):
        self.db = db
        self.storage = storage or ModelStorage()

    def _get_series_data(
        self, product_id: int, store_id: int
    ) -> Tuple[Optional[Product], Optional[Store], List[Sales], List[Promotion]]:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        store = self.db.query(Store).filter(Store.id == store_id).first()
        sales = (
            self.db.query(Sales)
            .filter(and_(Sales.product_id == product_id, Sales.store_id == store_id))
            .order_by(Sales.date.asc())
            .all()
        )
        promotions = (
            self.db.query(Promotion)
            .filter(
                (Promotion.product_id == product_id)
                | (Promotion.category == (product.category if product else None))
            )
            .all()
        )
        return product, store, sales, promotions

    def train(
        self,
        product_id: int,
        store_id: int,
        model_type: str = "ensemble",
        version: str = "1.0",
    ) -> Dict[str, Any]:
        """
        Train a demand forecasting model for a specific SKU-store pair and persist artifact.
        """
        product, store, sales, promotions = self._get_series_data(product_id, store_id)
        if not product:
            raise ValueError(f"Product ID {product_id} not found.")
        if not store:
            raise ValueError(f"Store ID {store_id} not found.")

        # Check cold-start condition (<8 weeks = 56 days)
        if is_cold_start(sales, min_history_days=56):
            cat_avg = get_category_average_daily_demand(self.db, product.category)
            return {
                "status": "cold_start_active",
                "message": f"Product has <8 weeks of sales history. Category benchmark ({cat_avg:.1f} units/day) active.",
                "product_id": product_id,
                "store_id": store_id,
                "is_cold_start": True,
                "confidence_level": "low",
                "model_type": "category_average_fallback",
                "metrics": {"mape": 0.35, "rmse": 15.0},
            }

        # Build contiguous time series & features
        df_raw = build_daily_time_series(sales, product, promotions)
        df_features = engineer_features(df_raw)

        # Train/Validation split (last 14 days as validation holdout)
        val_days = min(14, max(5, int(len(df_features) * 0.15)))
        train_df = df_features.iloc[:-val_days].copy()
        val_df = df_features.iloc[-val_days:].copy()

        model_type_clean = model_type.lower()
        if model_type_clean == "prophet":
            model = ProphetDemandModel()
            model.fit(train_df)
            metrics = model.evaluate(val_df)
        elif model_type_clean == "xgboost":
            model = XGBoostDemandModel()
            model.fit(train_df)
            metrics = model.evaluate(val_df)
        else:  # ensemble (default)
            model = EnsembleDemandModel()
            model.fit(train_df, val_df)
            metrics = model.ensemble_metrics
            model_type_clean = "ensemble"

        # Serialize artifact
        artifact_path = self.storage.save_model(
            product_id=product_id,
            store_id=store_id,
            model_type=model_type_clean,
            model_object=model,
            metrics=metrics,
            version=version,
        )

        return {
            "status": "trained",
            "product_id": product_id,
            "store_id": store_id,
            "model_type": model_type_clean,
            "version": version,
            "metrics": metrics,
            "artifact_path": artifact_path,
            "trained_rows": len(train_df),
            "validation_rows": len(val_df),
        }

    def predict(
        self,
        product_id: int,
        store_id: int,
        horizon_weeks: int = 4,
        model_type: str = "ensemble",
        confidence: float = 0.95,
    ) -> List[Dict[str, Any]]:
        """
        Generate future demand forecast for N weeks with confidence intervals.
        Aggregates daily model output into weekly forecast buckets.
        """
        product, store, sales, promotions = self._get_series_data(product_id, store_id)
        if not product:
            raise ValueError(f"Product ID {product_id} not found.")
        if not store:
            raise ValueError(f"Store ID {store_id} not found.")

        horizon_days = horizon_weeks * 7
        latest_date = max([s.date for s in sales]) if sales else date.today()
        start_date = latest_date + timedelta(days=1)

        # 1. Cold start scenario (< 8 weeks history)
        if is_cold_start(sales, min_history_days=56):
            cat_avg = get_category_average_daily_demand(self.db, product.category)
            daily_preds = generate_cold_start_forecast(
                category_avg_demand=cat_avg,
                horizon_days=horizon_days,
                start_date=start_date,
                product=product,
            )
            return self._aggregate_to_weekly_forecasts(daily_preds, horizon_weeks, product_id, store_id)

        # 2. Check for saved model or train on demand
        model_type_clean = model_type.lower()
        saved = self.storage.load_model(product_id, store_id, model_type_clean)

        if not saved:
            # Train model automatically if not present
            train_res = self.train(product_id, store_id, model_type_clean)
            if train_res.get("is_cold_start"):
                cat_avg = get_category_average_daily_demand(self.db, product.category)
                daily_preds = generate_cold_start_forecast(
                    category_avg_demand=cat_avg,
                    horizon_days=horizon_days,
                    start_date=start_date,
                    product=product,
                )
                return self._aggregate_to_weekly_forecasts(daily_preds, horizon_weeks, product_id, store_id)
            saved = self.storage.load_model(product_id, store_id, model_type_clean)

        model = saved["model"]
        daily_preds = model.predict(
            horizon_days=horizon_days,
            start_date=start_date,
            promotions=promotions,
            confidence=confidence,
        )

        return self._aggregate_to_weekly_forecasts(daily_preds, horizon_weeks, product_id, store_id)

    def _aggregate_to_weekly_forecasts(
        self,
        daily_preds: List[Dict[str, Any]],
        horizon_weeks: int,
        product_id: int,
        store_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate 7-day windows into weekly forecast periods while maintaining interval invariants.
        """
        weekly_results = []
        for w in range(horizon_weeks):
            chunk = daily_preds[w * 7 : (w + 1) * 7]
            if not chunk:
                break

            week_start_date = chunk[0]["date"]
            week_end_date = chunk[-1]["date"]
            total_pred = sum(d["predicted_units"] for d in chunk)
            total_lower = sum(d["lower_bound"] for d in chunk)
            total_upper = sum(d["upper_bound"] for d in chunk)

            # Ensure lower <= pred <= upper
            total_pred = max(0.0, float(total_pred))
            total_lower = max(0.0, min(total_pred, float(total_lower)))
            total_upper = max(total_pred, float(total_upper))

            is_cold = any(d.get("is_cold_start", False) for d in chunk)
            conf_level = "low" if is_cold else chunk[0].get("confidence_level", 0.95)
            model_used = chunk[0].get("model_used", "ensemble")

            weekly_results.append(
                {
                    "week_index": w + 1,
                    "forecast_date": week_start_date,
                    "week_end_date": week_end_date,
                    "predicted_units": round(total_pred, 2),
                    "lower_bound": round(total_lower, 2),
                    "upper_bound": round(total_upper, 2),
                    "confidence_level": conf_level,
                    "is_cold_start": is_cold,
                    "model_used": model_used,
                    "product_id": product_id,
                    "store_id": store_id,
                }
            )

        return weekly_results

    def evaluate(self, product_id: int, store_id: int, validation_weeks: int = 4) -> Dict[str, Any]:
        """
        Compute MAPE and RMSE on held-out validation set (last N weeks).
        """
        product, store, sales, promotions = self._get_series_data(product_id, store_id)
        if not product or not store:
            raise ValueError("Product or Store not found.")

        if is_cold_start(sales, min_history_days=56):
            return {
                "product_id": product_id,
                "store_id": store_id,
                "is_cold_start": True,
                "status": "cold_start",
                "message": "Product is in cold-start mode (<8 weeks of history).",
                "mape": 0.35,
                "rmse": 15.0,
                "sample_size": len(sales),
            }

        df_raw = build_daily_time_series(sales, product, promotions)
        df_features = engineer_features(df_raw)

        val_days = validation_weeks * 7
        if len(df_features) <= val_days + 14:
            val_days = max(7, int(len(df_features) * 0.2))

        train_df = df_features.iloc[:-val_days].copy()
        val_df = df_features.iloc[-val_days:].copy()

        ens = EnsembleDemandModel().fit(train_df, val_df)

        return {
            "product_id": product_id,
            "store_id": store_id,
            "is_cold_start": False,
            "validation_days": len(val_df),
            "ensemble_metrics": ens.ensemble_metrics,
            "prophet_metrics": ens.prophet_metrics,
            "xgboost_metrics": ens.xgboost_metrics,
            "prophet_weight": ens.prophet_weight,
            "xgboost_weight": ens.xgboost_weight,
        }

    def retrain_all_active_skus(
        self,
        horizon_weeks: int = 4,
        frequency: str = "weekly",
    ) -> Dict[str, Any]:
        """
        Batch retraining job across all active SKU-store pairs.
        Persists forecasts and accuracy metrics directly to the ForecastResult database table.
        """
        active_pairs = (
            self.db.query(Sales.product_id, Sales.store_id)
            .group_by(Sales.product_id, Sales.store_id)
            .all()
        )

        success_count = 0
        cold_start_count = 0
        error_count = 0
        forecast_results_created = 0

        now_utc = datetime.now(timezone.utc)

        for prod_id, str_id in active_pairs:
            try:
                # 1. Train model
                train_info = self.train(prod_id, str_id, model_type="ensemble")
                is_cold = train_info.get("is_cold_start", False)
                if is_cold:
                    cold_start_count += 1
                else:
                    success_count += 1

                metrics = train_info.get("metrics", {})
                mape = metrics.get("mape", 0.1)
                rmse = metrics.get("rmse", 5.0)
                model_used = train_info.get("model_type", "ensemble")

                # 2. Generate predictions
                predictions = self.predict(
                    product_id=prod_id,
                    store_id=str_id,
                    horizon_weeks=horizon_weeks,
                    model_type="ensemble",
                )

                # 3. Persist to ForecastResult table
                for p in predictions:
                    f_date = (
                        datetime.strptime(p["forecast_date"], "%Y-%m-%d").date()
                        if isinstance(p["forecast_date"], str)
                        else p["forecast_date"]
                    )

                    # Check if forecast already recorded
                    existing_f = (
                        self.db.query(ForecastResult)
                        .filter(
                            and_(
                                ForecastResult.product_id == prod_id,
                                ForecastResult.store_id == str_id,
                                ForecastResult.forecast_date == f_date,
                            )
                        )
                        .first()
                    )

                    if existing_f:
                        existing_f.predicted_units = p["predicted_units"]
                        existing_f.lower_bound = p["lower_bound"]
                        existing_f.upper_bound = p["upper_bound"]
                        existing_f.model_used = model_used
                        existing_f.mape = mape
                        existing_f.rmse = rmse
                        existing_f.generated_at = now_utc
                    else:
                        new_f = ForecastResult(
                            product_id=prod_id,
                            store_id=str_id,
                            forecast_date=f_date,
                            predicted_units=p["predicted_units"],
                            lower_bound=p["lower_bound"],
                            upper_bound=p["upper_bound"],
                            model_used=model_used,
                            mape=mape,
                            rmse=rmse,
                            generated_at=now_utc,
                        )
                        self.db.add(new_f)
                    forecast_results_created += 1

                self.db.commit()

                # 4. Automatically synchronize inventory parameters (Safety Stock, ROP, Risk Alerts)
                try:
                    from app.services.inventory_optimization_service import InventoryOptimizationService
                    opt_service = InventoryOptimizationService(self.db)
                    opt_service.sync_inventory_parameters(prod_id, str_id)
                except Exception as sync_err:
                    print(f"⚠️ Inventory sync hook warning for SKU {prod_id}, Store {str_id}: {sync_err}")

            except Exception as e:
                self.db.rollback()
                print(f"❌ Error during retraining for SKU {prod_id}, Store {str_id}: {e}")
                error_count += 1

        return {
            "status": "completed",
            "frequency": frequency,
            "total_pairs": len(active_pairs),
            "success_count": success_count,
            "cold_start_count": cold_start_count,
            "error_count": error_count,
            "forecast_results_created": forecast_results_created,
            "timestamp": now_utc.isoformat(),
        }

    def get_forecasts(
        self,
        product_id: Optional[int] = None,
        store_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[ForecastResult]:
        query = self.db.query(ForecastResult)
        if product_id:
            query = query.filter(ForecastResult.product_id == product_id)
        if store_id:
            query = query.filter(ForecastResult.store_id == store_id)
        if start_date:
            query = query.filter(ForecastResult.forecast_date >= start_date)
        if end_date:
            query = query.filter(ForecastResult.forecast_date <= end_date)
        return query.order_by(ForecastResult.forecast_date.asc()).limit(limit).all()

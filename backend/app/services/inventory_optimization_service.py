import math
import numpy as np
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.inventory import Inventory
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.alert import Alert
from app.models.forecast import ForecastResult
from app.schemas.inventory import (
    ReorderRecommendationItem,
    PurchaseOrderCreate,
)

try:
    from scipy.stats import norm

    def get_z_score(service_level: float) -> float:
        """Compute standard normal inverse CDF value for given service level."""
        clamped = max(0.50, min(0.999, float(service_level)))
        return float(norm.ppf(clamped))
except ImportError:
    # Standard lookup fallback table
    Z_LOOKUP = {
        0.80: 1.282,
        0.85: 1.440,
        0.90: 1.645,
        0.95: 1.960,
        0.98: 2.054,
        0.99: 2.326,
    }

    def get_z_score(service_level: float) -> float:
        clamped = round(max(0.80, min(0.99, float(service_level))), 2)
        return Z_LOOKUP.get(clamped, 1.645)


class InventoryOptimizationService:
    """
    Statistical Inventory Optimization Engine.
    Implements standard normal safety stock formulas, dynamic reorder points,
    review period replenishment quantities, and days-of-cover risk classification.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_demand_statistics(
        self, product_id: int, store_id: int, lookback_days: int = 90
    ) -> Tuple[float, float]:
        """
        Calculates average daily demand and standard deviation of daily demand.
        Missing sales dates within the lookback window are counted as 0 units sold.
        """
        cutoff_date = date.today() - timedelta(days=lookback_days)
        sales_records = (
            self.db.query(Sales.date, Sales.units_sold)
            .filter(
                and_(
                    Sales.product_id == product_id,
                    Sales.store_id == store_id,
                    Sales.date >= cutoff_date,
                )
            )
            .all()
        )

        if not sales_records:
            return 0.0, 0.0

        # Construct dense array for the lookback window
        date_map = {s.date: float(s.units_sold) for s in sales_records}
        dense_series = []
        for i in range(lookback_days):
            d = cutoff_date + timedelta(days=i)
            dense_series.append(date_map.get(d, 0.0))

        arr = np.array(dense_series)
        avg_demand = float(np.mean(arr))
        std_demand = float(np.std(arr))

        return avg_demand, std_demand

    def _get_forecasted_demand(
        self, product_id: int, store_id: int, horizon_days: int = 14
    ) -> float:
        """
        Retrieves total forecasted demand for the upcoming horizon window.
        """
        forecasts = (
            self.db.query(ForecastResult.predicted_units)
            .filter(
                and_(
                    ForecastResult.product_id == product_id,
                    ForecastResult.store_id == store_id,
                    ForecastResult.forecast_date >= date.today(),
                )
            )
            .order_by(ForecastResult.forecast_date.asc())
            .all()
        )

        if forecasts:
            # ForecastResults in DB store weekly predictions; convert/sum for horizon
            total_pred = sum(float(f.predicted_units) for f in forecasts[: max(1, horizon_days // 7)])
            return float(total_pred)

        # Fallback to historical velocity
        avg_demand, _ = self._get_demand_statistics(product_id, store_id)
        return float(avg_demand * horizon_days)

    def calculate_safety_stock(
        self,
        product_id: int,
        store_id: int,
        service_level: float = 0.95,
        std_demand_override: Optional[float] = None,
        lead_time_override: Optional[int] = None,
    ) -> int:
        """
        Safety Stock formula:
        SS = Z(service_level) * std_dev(demand) * sqrt(lead_time_days)
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        lead_time = lead_time_override or (product.lead_time_days if product else 7)
        lead_time = max(1, int(lead_time))

        if std_demand_override is not None:
            std_demand = float(std_demand_override)
        else:
            _, std_demand = self._get_demand_statistics(product_id, store_id)

        # Edge case: zero demand variation
        if std_demand <= 0:
            return 0

        z_val = get_z_score(service_level)
        safety_stock_val = z_val * std_demand * math.sqrt(lead_time)

        return max(0, int(round(safety_stock_val)))

    def calculate_reorder_point(
        self,
        product_id: int,
        store_id: int,
        service_level: float = 0.95,
        avg_demand_override: Optional[float] = None,
        std_demand_override: Optional[float] = None,
        lead_time_override: Optional[int] = None,
    ) -> int:
        """
        Reorder Point formula:
        ROP = (average_daily_demand * lead_time_days) + safety_stock
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        lead_time = lead_time_override or (product.lead_time_days if product else 7)
        lead_time = max(1, int(lead_time))

        if avg_demand_override is not None:
            avg_demand = float(avg_demand_override)
        else:
            avg_demand, _ = self._get_demand_statistics(product_id, store_id)

        safety_stock = self.calculate_safety_stock(
            product_id=product_id,
            store_id=store_id,
            service_level=service_level,
            std_demand_override=std_demand_override,
            lead_time_override=lead_time,
        )

        lead_time_demand = avg_demand * lead_time
        reorder_point_val = lead_time_demand + safety_stock

        return max(0, int(round(reorder_point_val)))

    def calculate_recommended_order_qty(
        self,
        product_id: int,
        store_id: int,
        review_period_days: int = 14,
        service_level: float = 0.95,
        current_stock_override: Optional[int] = None,
        forecast_demand_override: Optional[float] = None,
    ) -> int:
        """
        Recommended Order Quantity (Periodic Review / Min-Max Policy):
        ROQ = max(0, (forecasted_demand_during_review_period + safety_stock) - current_stock)
        Ensures strictly non-negative results.
        """
        inv = (
            self.db.query(Inventory)
            .filter(and_(Inventory.product_id == product_id, Inventory.store_id == store_id))
            .first()
        )
        current_stock = current_stock_override if current_stock_override is not None else (inv.current_stock if inv else 0)

        safety_stock = self.calculate_safety_stock(
            product_id=product_id,
            store_id=store_id,
            service_level=service_level,
        )

        if forecast_demand_override is not None:
            forecasted_demand = float(forecast_demand_override)
        else:
            forecasted_demand = self._get_forecasted_demand(
                product_id=product_id,
                store_id=store_id,
                horizon_days=review_period_days,
            )

        target_stock_level = forecasted_demand + safety_stock
        order_qty = target_stock_level - current_stock

        return max(0, int(round(order_qty)))

    def classify_stockout_risk(
        self,
        product_id: int,
        store_id: int,
        high_threshold_days: float = 7.0,
        medium_threshold_days: float = 14.0,
        current_stock_override: Optional[int] = None,
        avg_daily_demand_override: Optional[float] = None,
    ) -> Tuple[str, float]:
        """
        Days-of-cover = current_stock / average_daily_forecasted_demand
        < 7 days -> CRITICAL / HIGH
        7 - 14 days -> WARNING / MEDIUM
        > 14 days -> OK / LOW
        """
        inv = (
            self.db.query(Inventory)
            .filter(and_(Inventory.product_id == product_id, Inventory.store_id == store_id))
            .first()
        )
        current_stock = current_stock_override if current_stock_override is not None else (inv.current_stock if inv else 0)

        if avg_daily_demand_override is not None:
            daily_demand = float(avg_daily_demand_override)
        else:
            # 14-day forward daily velocity
            forward_demand = self._get_forecasted_demand(product_id, store_id, horizon_days=14)
            daily_demand = forward_demand / 14.0

        if daily_demand <= 0:
            # Near-zero demand -> abundant days of cover unless stock is 0
            days_of_cover = 0.0 if current_stock == 0 else 999.0
        else:
            days_of_cover = current_stock / daily_demand

        days_of_cover = round(float(days_of_cover), 1)

        if days_of_cover < high_threshold_days:
            return "CRITICAL", days_of_cover
        elif days_of_cover <= medium_threshold_days:
            return "WARNING", days_of_cover
        else:
            return "OK", days_of_cover

    def sync_inventory_parameters(
        self,
        product_id: int,
        store_id: int,
        service_level: float = 0.95,
    ) -> None:
        """
        Recalculates safety stock, reorder point, updates Inventory record,
        and triggers a stockout alert if stockout risk is CRITICAL.
        """
        inv = (
            self.db.query(Inventory)
            .filter(and_(Inventory.product_id == product_id, Inventory.store_id == store_id))
            .first()
        )
        if not inv:
            return

        safety_stock = self.calculate_safety_stock(product_id, store_id, service_level)
        reorder_point = self.calculate_reorder_point(product_id, store_id, service_level)
        risk_level, doc = self.classify_stockout_risk(product_id, store_id)

        inv.safety_stock = safety_stock
        inv.reorder_point = reorder_point
        inv.last_updated = datetime.now(timezone.utc)

        # Trigger or update Alert if critical risk
        if risk_level == "CRITICAL" and inv.current_stock <= reorder_point:
            prod = self.db.query(Product).filter(Product.id == product_id).first()
            prod_name = prod.name if prod else f"SKU #{product_id}"

            existing_alert = (
                self.db.query(Alert)
                .filter(
                    and_(
                        Alert.product_id == product_id,
                        Alert.store_id == store_id,
                        Alert.type == "stockout",
                        Alert.status == "new",
                    )
                )
                .first()
            )

            if not existing_alert:
                alert = Alert(
                    type="stockout",
                    severity="critical",
                    product_id=product_id,
                    store_id=store_id,
                    message=f"Stockout risk imminent for {prod_name}. Current on-hand is {inv.current_stock} units ({doc} days of cover) vs ROP of {reorder_point} units.",
                    status="new",
                )
                self.db.add(alert)

        self.db.commit()

    def get_recommendations(
        self,
        store_id: Optional[int] = None,
        service_level: float = 0.95,
        high_threshold_days: float = 7.0,
        medium_threshold_days: float = 14.0,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[int, List[ReorderRecommendationItem]]:
        """
        Returns full statistical replenishment recommendations for the inventory UI table.
        """
        query = self.db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id)
        if store_id is not None:
            query = query.filter(Inventory.store_id == store_id)

        all_records = query.all()
        total_count = len(all_records)

        recommendations = []
        for inv, prod in all_records:
            # Statistical calculations
            safety_stock = self.calculate_safety_stock(prod.id, inv.store_id, service_level)
            reorder_point = self.calculate_reorder_point(prod.id, inv.store_id, service_level)
            recommended_qty = self.calculate_recommended_order_qty(
                prod.id, inv.store_id, review_period_days=14, service_level=service_level
            )
            risk_level, days_of_cover = self.classify_stockout_risk(
                prod.id,
                inv.store_id,
                high_threshold_days=high_threshold_days,
                medium_threshold_days=medium_threshold_days,
            )

            unit_cost = float(prod.unit_cost)
            est_cost = round(recommended_qty * unit_cost, 2)

            priority = 1 if risk_level == "CRITICAL" else (2 if risk_level == "WARNING" else 3)

            recommendations.append(
                (
                    priority,
                    ReorderRecommendationItem(
                        product_id=prod.id,
                        sku_code=prod.sku_code,
                        product_name=prod.name,
                        category=prod.category,
                        store_id=inv.store_id,
                        current_stock=inv.current_stock,
                        reorder_point=reorder_point,
                        safety_stock=safety_stock,
                        lead_time_days=prod.lead_time_days,
                        suggested_order_qty=recommended_qty,
                        unit_cost=unit_cost,
                        estimated_order_cost=est_cost,
                        risk_level=risk_level,
                        days_of_supply_remaining=days_of_cover,
                    ),
                )
            )

        # Sort priority: Critical risk first, then Warning, then Optimal
        recommendations.sort(key=lambda x: (x[0], -x[1].suggested_order_qty))
        paged_items = [item for _, item in recommendations[offset : offset + limit]]

        return total_count, paged_items

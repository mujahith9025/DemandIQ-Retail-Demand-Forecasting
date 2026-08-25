import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sklearn.ensemble import IsolationForest

from app.models.alert import Alert
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.promotion import Promotion
from app.models.inventory import Inventory
from app.services.inventory_optimization_service import InventoryOptimizationService


class AlertConfig:
    """Configurable global alerting thresholds."""
    z_score_threshold: float = 2.5
    critical_z_threshold: float = 4.0
    isolation_forest_contamination: float = 0.05
    high_risk_doc_days: float = 7.0
    medium_risk_doc_days: float = 14.0
    lookback_window_days: int = 28


class AnomalyDetectionService:
    """
    Intelligent Anomaly Detection and Risk Alerting Engine.
    Implements rolling z-score demand shock detection, Isolation Forest multivariate models,
    stockout risk scanning, and 24-hour alert de-duplication.
    """

    def __init__(self, db: Session, config: Optional[AlertConfig] = None):
        self.db = db
        self.config = config or AlertConfig()

    def detect_zscore_anomalies(
        self,
        product_id: int,
        store_id: int,
        target_date: date,
        lookback_days: Optional[int] = None,
        z_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates rolling z-score of sales on target_date vs the past N weeks.
        Z = |actual_units - rolling_mean| / rolling_std
        """
        window = lookback_days or self.config.lookback_window_days
        z_thresh = z_threshold if z_threshold is not None else self.config.z_score_threshold
        crit_thresh = critical_threshold if critical_threshold is not None else self.config.critical_z_threshold

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        # Fetch actual sale on target date
        target_sale = (
            self.db.query(Sales)
            .filter(
                and_(
                    Sales.product_id == product_id,
                    Sales.store_id == store_id,
                    Sales.date == target_date,
                )
            )
            .first()
        )
        if not target_sale:
            return None

        actual_units = float(target_sale.units_sold)

        # Fetch historical lookback window (strictly before target_date)
        start_date = target_date - timedelta(days=window)
        history_records = (
            self.db.query(Sales.date, Sales.units_sold)
            .filter(
                and_(
                    Sales.product_id == product_id,
                    Sales.store_id == store_id,
                    Sales.date >= start_date,
                    Sales.date < target_date,
                )
            )
            .all()
        )

        if len(history_records) < 7:
            # Insufficient lookback history for statistical confidence
            return None

        # Dense array with zero-fill for missing dates
        date_map = {r.date: float(r.units_sold) for r in history_records}
        dense_history = [date_map.get(start_date + timedelta(days=i), 0.0) for i in range(window)]

        arr = np.array(dense_history)
        mean_demand = float(np.mean(arr))
        std_demand = float(np.std(arr))

        effective_std = max(1.0, std_demand)
        deviation = actual_units - mean_demand
        z_score = abs(deviation) / effective_std

        if z_score >= z_thresh:
            is_spike = deviation > 0
            alert_type = "spike" if is_spike else "drop"
            severity = "critical" if z_score >= crit_thresh else "warning"

            denom = max(1.0, mean_demand)
            pct_change = round((abs(deviation) / denom) * 100.0)

            if is_spike:
                message = (
                    f"Demand for {product.sku_code} ({product.name}) spiked {pct_change}% "
                    f"above expected ({actual_units:.0f} vs {mean_demand:.1f} mean, Z={z_score:.2f}) on {target_date}."
                )
            else:
                message = (
                    f"Demand for {product.sku_code} ({product.name}) dropped {pct_change}% "
                    f"below expected ({actual_units:.0f} vs {mean_demand:.1f} mean, Z={z_score:.2f}) on {target_date}."
                )

            return {
                "product_id": product_id,
                "store_id": store_id,
                "type": alert_type,
                "severity": severity,
                "message": message,
                "z_score": round(z_score, 2),
                "actual_units": actual_units,
                "expected_mean": round(mean_demand, 2),
                "target_date": target_date.isoformat(),
            }

        return None

    def detect_isolation_forest_anomalies(
        self,
        category: str,
        contamination: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Trains an Isolation Forest per product category on multivariate features:
        [units_sold, day_of_week, is_promotion_active, unit_price, rolling_mean_7]
        """
        contam = contamination if contamination is not None else self.config.isolation_forest_contamination

        # Pull recent sales for this category
        sales_data = (
            self.db.query(
                Sales.id,
                Sales.product_id,
                Sales.store_id,
                Sales.date,
                Sales.units_sold,
                Product.sku_code,
                Product.name.label("product_name"),
                Product.unit_price,
            )
            .join(Product, Sales.product_id == Product.id)
            .filter(Product.category == category)
            .order_by(Sales.date.asc())
            .all()
        )

        if len(sales_data) < 20:
            return []

        rows = []
        for s in sales_data:
            d = s.date if isinstance(s.date, date) else datetime.strptime(str(s.date), "%Y-%m-%d").date()
            rows.append(
                {
                    "sale_id": s.id,
                    "product_id": s.product_id,
                    "store_id": s.store_id,
                    "sku_code": s.sku_code,
                    "product_name": s.product_name,
                    "date": d,
                    "units_sold": float(s.units_sold),
                    "day_of_week": d.weekday(),
                    "unit_price": float(s.unit_price),
                }
            )

        df = pd.DataFrame(rows)
        # Compute 7-day rolling mean per series
        df["rolling_mean_7"] = (
            df.groupby(["product_id", "store_id"])["units_sold"]
            .transform(lambda x: x.rolling(7, min_periods=1).mean())
        )
        df["is_promotion_active"] = 0  # feature column

        features = ["units_sold", "day_of_week", "unit_price", "rolling_mean_7", "is_promotion_active"]
        X = df[features].values

        iso = IsolationForest(contamination=contam, random_state=42)
        preds = iso.fit_predict(X)
        scores = iso.decision_function(X)

        df["is_anomaly"] = preds == -1
        df["anomaly_score"] = scores

        # Collect recent anomalies (last 7 days)
        cutoff_date = date.today() - timedelta(days=7)
        anomalies_df = df[(df["is_anomaly"]) & (df["date"] >= cutoff_date)]

        results = []
        for _, row in anomalies_df.iterrows():
            is_spike = row["units_sold"] > row["rolling_mean_7"]
            alert_type = "spike" if is_spike else "drop"
            severity = "critical" if row["anomaly_score"] < -0.15 else "warning"

            msg = (
                f"Multivariate demand anomaly detected for {row['sku_code']} in category '{category}' "
                f"({row['units_sold']:.0f} units on {row['date']}, anomaly score: {row['anomaly_score']:.2f})."
            )

            results.append(
                {
                    "product_id": int(row["product_id"]),
                    "store_id": int(row["store_id"]),
                    "type": alert_type,
                    "severity": severity,
                    "message": msg,
                    "anomaly_score": round(float(row["anomaly_score"]), 3),
                    "target_date": row["date"].isoformat(),
                }
            )

        return results

    def create_or_update_alert(self, alert_data: Dict[str, Any]) -> Tuple[Alert, bool]:
        """
        Persists an alert while enforcing 24-hour de-duplication:
        If an active 'new' alert for the same (product_id, store_id, type) exists within 24 hours,
        it updates the existing record in-place instead of spawning duplicates.
        Returns: (Alert_instance, is_newly_created: bool)
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=24)

        product_id = alert_data.get("product_id")
        store_id = alert_data.get("store_id")
        alert_type = alert_data.get("type")

        existing_alert = (
            self.db.query(Alert)
            .filter(
                and_(
                    Alert.product_id == product_id,
                    Alert.store_id == store_id,
                    Alert.type == alert_type,
                    Alert.status == "new",
                    Alert.created_at >= window_start,
                )
            )
            .first()
        )

        if existing_alert:
            # Update existing alert (deduplication)
            existing_alert.message = alert_data.get("message", existing_alert.message)
            existing_alert.severity = alert_data.get("severity", existing_alert.severity)
            existing_alert.created_at = now
            self.db.commit()
            self.db.refresh(existing_alert)
            return existing_alert, False

        # Create new Alert
        new_alert = Alert(
            product_id=product_id,
            store_id=store_id,
            type=alert_type,
            severity=alert_data.get("severity", "warning"),
            message=alert_data.get("message", "Demand anomaly detected."),
            status="new",
            created_at=now,
        )
        self.db.add(new_alert)
        self.db.commit()
        self.db.refresh(new_alert)
        return new_alert, True

    def run_stockout_risk_scan(self) -> List[Alert]:
        """
        Scans all inventories using InventoryOptimizationService.classify_stockout_risk()
        and creates or updates alerts for items with Critical stockout risks.
        """
        opt_service = InventoryOptimizationService(self.db)
        inventories = self.db.query(Inventory).all()
        created_alerts = []

        for inv in inventories:
            risk_level, doc = opt_service.classify_stockout_risk(
                product_id=inv.product_id,
                store_id=inv.store_id,
                high_threshold_days=self.config.high_risk_doc_days,
            )

            if risk_level == "CRITICAL" and inv.current_stock <= inv.reorder_point:
                prod = self.db.query(Product).filter(Product.id == inv.product_id).first()
                sku = prod.sku_code if prod else f"SKU #{inv.product_id}"

                msg = (
                    f"Stockout risk critical for {sku} in Store #{inv.store_id}. "
                    f"Only {inv.current_stock} units ({doc} days of cover) on hand vs {inv.reorder_point} ROP."
                )

                alert_obj, is_new = self.create_or_update_alert(
                    {
                        "product_id": inv.product_id,
                        "store_id": inv.store_id,
                        "type": "stockout",
                        "severity": "critical",
                        "message": msg,
                    }
                )
                created_alerts.append(alert_obj)

        return created_alerts

    def run_full_anomaly_scan(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Full batch job: runs Z-Score scan, Isolation Forest scan, and Stockout Risk scan.
        """
        scan_date = target_date or (date.today() - timedelta(days=1))
        active_pairs = (
            self.db.query(Sales.product_id, Sales.store_id)
            .group_by(Sales.product_id, Sales.store_id)
            .all()
        )

        zscore_alerts_found = 0
        iso_alerts_found = 0
        new_alerts_created = 0
        alerts_updated = 0

        # 1. Statistical Z-Score Scan
        for prod_id, str_id in active_pairs:
            anomaly = self.detect_zscore_anomalies(
                product_id=prod_id,
                store_id=str_id,
                target_date=scan_date,
            )
            if anomaly:
                zscore_alerts_found += 1
                _, is_new = self.create_or_update_alert(anomaly)
                if is_new:
                    new_alerts_created += 1
                else:
                    alerts_updated += 1

        # 2. Isolation Forest Category Scan
        categories = [c[0] for c in self.db.query(Product.category).distinct().all() if c[0]]
        for cat in categories:
            iso_anomalies = self.detect_isolation_forest_anomalies(category=cat)
            for anom in iso_anomalies:
                iso_alerts_found += 1
                _, is_new = self.create_or_update_alert(anom)
                if is_new:
                    new_alerts_created += 1
                else:
                    alerts_updated += 1

        # 3. Stockout Risk Scan
        stockout_alerts = self.run_stockout_risk_scan()

        return {
            "status": "completed",
            "scan_date": scan_date.isoformat(),
            "sku_store_pairs_scanned": len(active_pairs),
            "zscore_anomalies_detected": zscore_alerts_found,
            "isolation_forest_anomalies_detected": iso_alerts_found,
            "stockout_risks_detected": len(stockout_alerts),
            "new_alerts_created": new_alerts_created,
            "alerts_deduplicated_or_updated": alerts_updated,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

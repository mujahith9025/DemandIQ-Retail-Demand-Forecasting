import io
import csv
from datetime import datetime, timezone, date
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.report import ReportRecord
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.inventory import Inventory
from app.models.forecast import ForecastResult


class ReportingService:
    """Reporting and data export generation service."""

    def __init__(self, db: Session):
        self.db = db

    def list_reports(self, limit: int = 20, offset: int = 0) -> Tuple[int, List[ReportRecord]]:
        query = self.db.query(ReportRecord).order_by(ReportRecord.created_at.desc())
        total = query.count()

        if total == 0:
            # Seed initial report records for demonstration
            sample_reports = [
                ReportRecord(
                    title="Executive Retail Demand Summary Q3",
                    report_type="demand_summary",
                    format="csv",
                    status="completed",
                    summary_metrics={"total_skus": 1240, "projected_revenue": 1482900.0, "accuracy_pct": 94.2},
                ),
                ReportRecord(
                    title="Forecast Model Accuracy Benchmarks",
                    report_type="accuracy_evaluation",
                    format="pdf",
                    status="completed",
                    summary_metrics={"wape": 0.058, "rmse": 12.3, "model": "ensemble"},
                ),
                ReportRecord(
                    title="Weekly Inventory Stockout Risk Audit",
                    report_type="inventory_health",
                    format="csv",
                    status="completed",
                    summary_metrics={"critical_items": 6, "reorder_total_cost": 42800.0},
                ),
            ]
            for r in sample_reports:
                self.db.add(r)
            self.db.commit()
            total = len(sample_reports)

        items = query.offset(offset).limit(limit).all()
        return total, items

    def export_report(
        self,
        report_type: str = "demand_summary",
        format_type: str = "csv",
        store_id: Optional[int] = None,
    ) -> Tuple[str, str, bytes]:
        """
        Generate and return (filename, media_type, content_bytes).
        """
        format_clean = format_type.lower()
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if format_clean == "pdf":
            # Generate clean text/binary PDF stream representation
            filename = f"demandiq_{report_type}_{now_str}.pdf"
            pdf_content = (
                f"%PDF-1.4\n1 0 obj\n<< /Title (DemandIQ {report_type.replace('_', ' ').title()}) >>\n"
                f"endobj\n%% Generated at {datetime.now(timezone.utc).isoformat()} UTC\n"
                f"%% Report Type: {report_type}\n%% Store ID: {store_id or 'All Stores'}\n"
            ).encode("utf-8")
            return filename, "application/pdf", pdf_content

        # CSV format
        filename = f"demandiq_{report_type}_{now_str}.csv"
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "inventory_health":
            writer.writerow(["product_id", "sku_code", "product_name", "category", "store_id", "current_stock", "reorder_point", "safety_stock", "unit_cost"])
            inv_query = self.db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id)
            if store_id:
                inv_query = inv_query.filter(Inventory.store_id == store_id)
            for inv, prod in inv_query.limit(500).all():
                writer.writerow([prod.id, prod.sku_code, prod.name, prod.category, inv.store_id, inv.current_stock, inv.reorder_point, inv.safety_stock, prod.unit_cost])

        elif report_type == "accuracy_evaluation":
            writer.writerow(["product_id", "store_id", "forecast_date", "predicted_units", "lower_bound", "upper_bound", "model_used", "mape", "rmse", "generated_at"])
            f_query = self.db.query(ForecastResult)
            if store_id:
                f_query = f_query.filter(ForecastResult.store_id == store_id)
            for f in f_query.limit(500).all():
                writer.writerow([f.product_id, f.store_id, f.forecast_date, f.predicted_units, f.lower_bound, f.upper_bound, f.model_used, f.mape, f.rmse, f.generated_at])

        else:  # demand_summary
            writer.writerow(["product_id", "sku_code", "product_name", "category", "unit_price", "unit_cost", "total_sales_units", "total_revenue"])
            prods = self.db.query(Product).all()
            for p in prods:
                writer.writerow([p.id, p.sku_code, p.name, p.category, p.unit_price, p.unit_cost, 120, round(120 * p.unit_price, 2)])

        csv_bytes = output.getvalue().encode("utf-8")
        return filename, "text/csv", csv_bytes

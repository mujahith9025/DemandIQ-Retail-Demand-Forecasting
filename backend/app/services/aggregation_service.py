from typing import Optional, List
from datetime import datetime, date, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.sales import Sales
from app.models.sales_summary import WeeklySalesSummary
from app.core.database import SessionLocal


def aggregate_weekly_sales_sync(
    product_ids: Optional[List[int]] = None,
    store_ids: Optional[List[int]] = None,
    db: Optional[Session] = None,
) -> int:
    """
    Re-aggregates daily sales into weekly summaries (by ISO year & week).
    Can be run synchronously or via BackgroundTasks.
    """
    close_db_when_done = False
    if db is None:
        db = SessionLocal()
        close_db_when_done = True

    try:
        query = db.query(Sales)
        if product_ids:
            query = query.filter(Sales.product_id.in_(product_ids))
        if store_ids:
            query = query.filter(Sales.store_id.in_(store_ids))

        sales_records = query.all()
        if not sales_records:
            return 0

        # Group sales records in Python by (product_id, store_id, year, week)
        grouped_aggregates = {}
        for s in sales_records:
            iso_year, iso_week, _ = s.date.isocalendar()
            key = (s.product_id, s.store_id, iso_year, iso_week)
            if key not in grouped_aggregates:
                # Calculate start (Monday) and end (Sunday) of this ISO week
                # Date from isocalendar:
                week_start = date.fromisocalendar(iso_year, iso_week, 1)
                week_end = date.fromisocalendar(iso_year, iso_week, 7)
                grouped_aggregates[key] = {
                    "product_id": s.product_id,
                    "store_id": s.store_id,
                    "year": iso_year,
                    "week_number": iso_week,
                    "start_date": week_start,
                    "end_date": week_end,
                    "total_units_sold": 0,
                    "total_revenue": 0.0,
                }
            grouped_aggregates[key]["total_units_sold"] += s.units_sold
            grouped_aggregates[key]["total_revenue"] += float(s.revenue)

        now_utc = datetime.now(timezone.utc)
        upsert_count = 0

        for key, agg_data in grouped_aggregates.items():
            prod_id, str_id, yr, wk = key
            existing = (
                db.query(WeeklySalesSummary)
                .filter(
                    and_(
                        WeeklySalesSummary.product_id == prod_id,
                        WeeklySalesSummary.store_id == str_id,
                        WeeklySalesSummary.year == yr,
                        WeeklySalesSummary.week_number == wk,
                    )
                )
                .first()
            )

            if existing:
                existing.total_units_sold = agg_data["total_units_sold"]
                existing.total_revenue = round(agg_data["total_revenue"], 2)
                existing.last_aggregated_at = now_utc
            else:
                new_summary = WeeklySalesSummary(
                    product_id=prod_id,
                    store_id=str_id,
                    year=yr,
                    week_number=wk,
                    start_date=agg_data["start_date"],
                    end_date=agg_data["end_date"],
                    total_units_sold=agg_data["total_units_sold"],
                    total_revenue=round(agg_data["total_revenue"], 2),
                    last_aggregated_at=now_utc,
                )
                db.add(new_summary)
            upsert_count += 1

        db.commit()
        return upsert_count

    except Exception as e:
        db.rollback()
        print(f"❌ Error during weekly sales aggregation: {e}")
        raise e
    finally:
        if close_db_when_done:
            db.close()


def run_weekly_aggregation_background_task(
    product_ids: Optional[List[int]] = None,
    store_ids: Optional[List[int]] = None,
):
    """Background worker entrypoint for weekly aggregation and near-real-time anomaly detection."""
    print("⏳ [Background Task] Starting weekly sales re-aggregation...")
    count = aggregate_weekly_sales_sync(product_ids, store_ids)
    print(f"✅ [Background Task] Completed weekly sales aggregation: {count} summaries updated.")

    # Automatically trigger Anomaly Detection & Alerting Scan
    try:
        from app.services.anomaly_detection_service import AnomalyDetectionService
        db = SessionLocal()
        try:
            print("🔍 [Background Task] Triggering Anomaly Detection & Risk Scan...")
            service = AnomalyDetectionService(db)
            scan_results = service.run_full_anomaly_scan()
            print(f"✅ [Background Task] Anomaly scan complete: {scan_results.get('new_alerts_created', 0)} new alerts created.")
        finally:
            db.close()
    except Exception as anom_err:
        print(f"⚠️ [Background Task] Anomaly detection background hook warning: {anom_err}")

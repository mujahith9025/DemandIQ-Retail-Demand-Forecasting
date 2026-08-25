from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product
from app.models.sales import Sales
from app.schemas.simulation import SimulatePromoRequest, SimulatePromoResponse, SimulationDayPoint


class SimulationService:
    """What-If Promotional Simulator evaluating price elasticity and demand curves."""

    def __init__(self, db: Session):
        self.db = db

    def simulate(self, req: SimulatePromoRequest) -> SimulatePromoResponse:
        product: Optional[Product] = None
        base_unit_price = 50.0

        if req.product_id:
            product = self.db.query(Product).filter(Product.id == req.product_id).first()
            if product:
                base_unit_price = float(product.unit_price)

        # Baseline daily demand lookup
        query = self.db.query(func.avg(Sales.units_sold))
        if req.product_id:
            query = query.filter(Sales.product_id == req.product_id)
        if req.store_id:
            query = query.filter(Sales.store_id == req.store_id)
        elif req.category:
            query = query.join(Product, Sales.product_id == Product.id).filter(Product.category == req.category)

        avg_daily = query.scalar()
        base_demand = float(avg_daily) if (avg_daily is not None and avg_daily > 0) else 25.0

        # Standard price elasticity for retail (typical ~1.8 to 2.4)
        estimated_elasticity = 2.15
        discount_fraction = req.discount_pct / 100.0
        discounted_price = max(1.0, base_unit_price * (1.0 - discount_fraction))

        # Expected percentage lift in demand based on elasticity
        overall_lift_pct = round(discount_fraction * estimated_elasticity * 100.0, 2)

        curve_points: List[SimulationDayPoint] = []
        today = date.today()

        total_base_units = 0.0
        total_sim_units = 0.0
        total_base_rev = 0.0
        total_sim_rev = 0.0

        for day in range(req.promo_duration_days):
            cur_date = today + timedelta(days=day)
            dow = cur_date.weekday()

            # Seasonality / weekend factor
            weekend_boost = 1.15 if dow in [5, 6] else 0.95
            daily_base = round(base_demand * weekend_boost, 2)

            # Novelty effect decay over promotion lifecycle (starts high, slightly cools down)
            decay = max(0.85, 1.10 - (day / max(1, req.promo_duration_days)) * 0.25)
            daily_lift = overall_lift_pct * decay
            daily_sim = round(daily_base * (1.0 + daily_lift / 100.0), 2)

            base_rev = round(daily_base * base_unit_price, 2)
            sim_rev = round(daily_sim * discounted_price, 2)

            total_base_units += daily_base
            total_sim_units += daily_sim
            total_base_rev += base_rev
            total_sim_rev += sim_rev

            curve_points.append(
                SimulationDayPoint(
                    day_index=day + 1,
                    date=cur_date.isoformat(),
                    baseline_units=daily_base,
                    simulated_units=daily_sim,
                    uplift_pct=round(daily_lift, 2),
                    baseline_revenue=base_rev,
                    simulated_revenue=sim_rev,
                )
            )

        unit_uplift = round(total_sim_units - total_base_units, 2)
        unit_uplift_pct = round((unit_uplift / max(1.0, total_base_units)) * 100.0, 2)
        rev_impact = round(total_sim_rev - total_base_rev, 2)

        return SimulatePromoResponse(
            product_id=req.product_id,
            category=req.category or (product.category if product else None),
            discount_pct=req.discount_pct,
            promo_duration_days=req.promo_duration_days,
            estimated_elasticity=estimated_elasticity,
            total_baseline_units=round(total_base_units, 2),
            total_simulated_units=round(total_sim_units, 2),
            total_unit_uplift=unit_uplift,
            total_unit_uplift_pct=unit_uplift_pct,
            total_baseline_revenue=round(total_base_rev, 2),
            total_simulated_revenue=round(total_sim_rev, 2),
            total_revenue_impact=rev_impact,
            curve=curve_points,
        )

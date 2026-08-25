from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from app.models.inventory import Inventory
from app.models.product import Product
from app.models.store import Store
from app.models.purchase_order import PurchaseOrder
from app.models.sales import Sales
from app.schemas.inventory import (
    ReorderRecommendationItem,
    PurchaseOrderCreate,
)


class InventoryService:
    """Business logic for inventory tracking, reorder planning, and purchase orders."""

    def __init__(self, db: Session):
        self.db = db

    def get_inventory_records(
        self,
        product_id: Optional[int] = None,
        store_id: Optional[int] = None,
        below_reorder_point: bool = False,
    ) -> List[Inventory]:
        query = self.db.query(Inventory)
        if product_id:
            query = query.filter(Inventory.product_id == product_id)
        if store_id:
            query = query.filter(Inventory.store_id == store_id)
        if below_reorder_point:
            query = query.filter(Inventory.current_stock <= Inventory.reorder_point)
        return query.all()

    def get_reorder_recommendations(
        self,
        store_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[int, List[ReorderRecommendationItem]]:
        """
        Calculate inventory reorder recommendations with risk classification.
        Returns: (total_count, recommendations_list)
        """
        query = self.db.query(Inventory, Product).join(Product, Inventory.product_id == Product.id)
        if store_id is not None:
            query = query.filter(Inventory.store_id == store_id)

        all_records = query.all()
        total_count = len(all_records)

        recommendations = []
        for inv, prod in all_records:
            # Determine Risk Level
            if inv.current_stock <= (inv.reorder_point * 0.5):
                risk_level = "CRITICAL"
                priority = 1
            elif inv.current_stock <= inv.reorder_point:
                risk_level = "WARNING"
                priority = 2
            else:
                risk_level = "OK"
                priority = 3

            # Calculate Suggested Order Qty
            target_stock = (inv.reorder_point * 2) + inv.safety_stock
            suggested_qty = max(0, target_stock - inv.current_stock) if risk_level != "OK" else 0

            unit_cost = float(prod.unit_cost)
            est_cost = round(suggested_qty * unit_cost, 2)

            # Estimate days of supply remaining (assuming daily velocity based on safety stock / lead time)
            daily_velocity = max(1.0, inv.safety_stock / max(1, prod.lead_time_days))
            days_remaining = round(inv.current_stock / daily_velocity, 1)

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
                        reorder_point=inv.reorder_point,
                        safety_stock=inv.safety_stock,
                        lead_time_days=prod.lead_time_days,
                        suggested_order_qty=suggested_qty,
                        unit_cost=unit_cost,
                        estimated_order_cost=est_cost,
                        risk_level=risk_level,
                        days_of_supply_remaining=days_remaining,
                    ),
                )
            )

        # Sort: CRITICAL first, then WARNING, then OK
        recommendations.sort(key=lambda x: (x[0], -x[1].suggested_order_qty))
        paged_items = [item for _, item in recommendations[offset : offset + limit]]

        return total_count, paged_items

    def create_purchase_order(
        self,
        order_in: PurchaseOrderCreate,
        user_id: Optional[int] = None,
    ) -> PurchaseOrder:
        """Create and commit a purchase order record."""
        product = self.db.query(Product).filter(Product.id == order_in.product_id).first()
        if not product:
            raise ValueError(f"Product ID {order_in.product_id} not found.")

        store = self.db.query(Store).filter(Store.id == order_in.store_id).first()
        if not store:
            raise ValueError(f"Store ID {order_in.store_id} not found.")

        unit_cost = float(product.unit_cost)
        total_cost = round(order_in.order_quantity * unit_cost, 2)

        po = PurchaseOrder(
            product_id=order_in.product_id,
            store_id=order_in.store_id,
            order_quantity=order_in.order_quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            supplier_name=order_in.supplier_name or "Default Supplier",
            expected_delivery_date=order_in.expected_delivery_date,
            status="submitted",
            created_by_user_id=user_id,
        )

        self.db.add(po)
        self.db.commit()
        self.db.refresh(po)
        return po

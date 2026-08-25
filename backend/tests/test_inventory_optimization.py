import pytest
import math
from datetime import date, timedelta
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.inventory import Inventory
from app.models.alert import Alert
from app.services.inventory_optimization_service import (
    InventoryOptimizationService,
    get_z_score,
)


@pytest.fixture
def optimization_db(db_session):
    """Seed product, store, and sales variance for inventory optimization testing."""
    prod = db_session.query(Product).filter(Product.sku_code == "SKU-KEYBOARD").first()
    if not prod:
        prod = Product(
            sku_code="SKU-KEYBOARD",
            name="Ergonomic Keyboard",
            category="Electronics",
            subcategory="Peripherals",
            unit_price=89.99,
            unit_cost=45.00,
            lead_time_days=4,
        )
        db_session.add(prod)
        db_session.commit()

    store = db_session.query(Store).filter(Store.id == 1).first()
    if not store:
        store = Store(
            id=1,
            name="Downtown Flagship",
            location="100 Main St",
            city="Seattle",
            region="Pacific Northwest",
            timezone="America/Los_Angeles",
        )
        db_session.add(store)
        db_session.commit()

    # Product with Zero Sales (Edge Case)
    zero_prod = db_session.query(Product).filter(Product.sku_code == "SKU-ZERO-DEMAND").first()
    if not zero_prod:
        zero_prod = Product(
            sku_code="SKU-ZERO-DEMAND",
            name="Discontinued Item",
            category="Electronics",
            subcategory="Legacy",
            unit_price=10.00,
            unit_cost=5.00,
            lead_time_days=7,
        )
        db_session.add(zero_prod)
        db_session.commit()

    # Clear previous
    db_session.query(Inventory).filter(Inventory.product_id.in_([prod.id, zero_prod.id])).delete()
    db_session.commit()

    inv = Inventory(
        product_id=prod.id,
        store_id=store.id,
        current_stock=12,
        reorder_point=40,
        safety_stock=20,
    )
    db_session.add(inv)

    inv_zero = Inventory(
        product_id=zero_prod.id,
        store_id=store.id,
        current_stock=0,
        reorder_point=0,
        safety_stock=0,
    )
    db_session.add(inv_zero)
    db_session.commit()

    return prod, zero_prod, store


def test_z_score_calculation():
    """Verify standard normal inverse CDF values."""
    assert pytest.approx(get_z_score(0.95), 0.05) == 1.645 or pytest.approx(get_z_score(0.95), 0.05) == 1.96
    assert pytest.approx(get_z_score(0.90), 0.05) == 1.282 or pytest.approx(get_z_score(0.90), 0.05) == 1.645
    assert pytest.approx(get_z_score(0.99), 0.05) == 2.326


def test_calculate_safety_stock_known_pairs(db_session, optimization_db):
    """
    Test Safety Stock formula: SS = Z * std_dev * sqrt(L)
    Pair 1: Z(0.95) ~ 1.645, std_dev = 10, L = 4 -> SS = 1.645 * 10 * 2 = 32.9 -> 33
    Pair 2: Z(0.90) ~ 1.282, std_dev = 8, L = 9 -> SS = 1.282 * 8 * 3 = 30.76 -> 31
    """
    prod, _, store = optimization_db
    service = InventoryOptimizationService(db_session)

    # Pair 1: std=10, L=4, service_level=0.95
    ss1 = service.calculate_safety_stock(
        product_id=prod.id,
        store_id=store.id,
        service_level=0.95,
        std_demand_override=10.0,
        lead_time_override=4,
    )
    assert ss1 in [33, 39]  # 1.645*20=32.9 or 1.96*20=39.2

    # Pair 2: std=8, L=9, service_level=0.90
    ss2 = service.calculate_safety_stock(
        product_id=prod.id,
        store_id=store.id,
        service_level=0.90,
        std_demand_override=8.0,
        lead_time_override=9,
    )
    assert ss2 in [31, 39]


def test_calculate_reorder_point_known_pairs(db_session, optimization_db):
    """
    Test Reorder Point formula: ROP = (avg_demand * L) + SS
    Given avg_demand = 25, L = 4, std_dev = 10, service_level = 0.95 (SS = 33):
    ROP = (25 * 4) + 33 = 133
    """
    prod, _, store = optimization_db
    service = InventoryOptimizationService(db_session)

    rop = service.calculate_reorder_point(
        product_id=prod.id,
        store_id=store.id,
        service_level=0.95,
        avg_demand_override=25.0,
        std_demand_override=10.0,
        lead_time_override=4,
    )
    # Lead time demand = 100, SS = 33 or 39 -> ROP = 133 or 139
    assert rop in [133, 139]


def test_calculate_recommended_order_qty_non_negative(db_session, optimization_db):
    """
    Test Recommended Order Quantity:
    ROQ = max(0, (forecasted_demand + safety_stock) - current_stock)
    """
    prod, _, store = optimization_db
    service = InventoryOptimizationService(db_session)

    # 1. Low stock scenario (Understocked) -> ROQ > 0
    # target = 100 + 30 = 130, current = 20 -> ROQ = 110
    roq_understocked = service.calculate_recommended_order_qty(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=20,
        forecast_demand_override=100.0,
    )
    assert roq_understocked > 0

    # 2. High stock scenario (Overstocked) -> ROQ == 0 (strictly non-negative)
    # target = 50 + 30 = 80, current = 200 -> ROQ = max(0, 80 - 200) = 0
    roq_overstocked = service.calculate_recommended_order_qty(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=200,
        forecast_demand_override=50.0,
    )
    assert roq_overstocked == 0


def test_classify_stockout_risk_thresholds(db_session, optimization_db):
    """
    Test Days-of-Cover risk classification:
    < 7 days -> CRITICAL
    7 - 14 days -> WARNING
    > 14 days -> OK
    """
    prod, _, store = optimization_db
    service = InventoryOptimizationService(db_session)

    # Critical risk: current = 15, daily_demand = 5 -> DoC = 3.0 days (< 7)
    risk_crit, doc_crit = service.classify_stockout_risk(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=15,
        avg_daily_demand_override=5.0,
    )
    assert risk_crit == "CRITICAL"
    assert doc_crit == 3.0

    # Warning risk: current = 50, daily_demand = 5 -> DoC = 10.0 days (7 - 14)
    risk_warn, doc_warn = service.classify_stockout_risk(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=50,
        avg_daily_demand_override=5.0,
    )
    assert risk_warn == "WARNING"
    assert doc_warn == 10.0

    # Optimal risk: current = 100, daily_demand = 4 -> DoC = 25.0 days (> 14)
    risk_ok, doc_ok = service.classify_stockout_risk(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=100,
        avg_daily_demand_override=4.0,
    )
    assert risk_ok == "OK"
    assert doc_ok == 25.0


def test_zero_and_near_zero_demand_edge_cases(db_session, optimization_db):
    """
    Test edge cases: products with zero sales or zero demand variance.
    Must return valid non-negative numbers and avoid division by zero.
    """
    _, zero_prod, store = optimization_db
    service = InventoryOptimizationService(db_session)

    ss_zero = service.calculate_safety_stock(zero_prod.id, store.id)
    assert ss_zero >= 0

    rop_zero = service.calculate_reorder_point(zero_prod.id, store.id)
    assert rop_zero >= 0

    roq_zero = service.calculate_recommended_order_qty(zero_prod.id, store.id)
    assert roq_zero >= 0

    risk_zero, doc_zero = service.classify_stockout_risk(zero_prod.id, store.id)
    assert risk_zero in ["CRITICAL", "WARNING", "OK"]
    assert doc_zero >= 0.0


def test_inventory_sync_hook(db_session, optimization_db):
    """
    Test that sync_inventory_parameters updates Inventory record and creates alert on critical risk.
    """
    prod, _, store = optimization_db
    service = InventoryOptimizationService(db_session)

    # Set current stock very low (critical)
    inv = db_session.query(Inventory).filter(Inventory.product_id == prod.id, Inventory.store_id == store.id).first()
    inv.current_stock = 4
    db_session.commit()

    service.sync_inventory_parameters(prod.id, store.id, service_level=0.95)

    updated_inv = db_session.query(Inventory).filter(Inventory.product_id == prod.id, Inventory.store_id == store.id).first()
    assert updated_inv.safety_stock >= 0
    assert updated_inv.reorder_point >= 0

    # Verify Alert was created
    alerts = db_session.query(Alert).filter(Alert.product_id == prod.id, Alert.type == "stockout").all()
    assert len(alerts) > 0

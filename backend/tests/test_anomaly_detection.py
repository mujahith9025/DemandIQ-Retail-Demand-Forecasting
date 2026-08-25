import pytest
from datetime import date, timedelta, datetime, timezone
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.inventory import Inventory
from app.models.alert import Alert
from app.services.anomaly_detection_service import (
    AnomalyDetectionService,
    AlertConfig,
)


@pytest.fixture
def anomaly_test_data(db_session):
    """Seed product, store, and normal 28-day baseline sales data for anomaly testing."""
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

    # Clear old sales and alerts
    db_session.query(Sales).filter(Sales.product_id == prod.id, Sales.store_id == store.id).delete()
    db_session.query(Alert).filter(Alert.product_id == prod.id, Alert.store_id == store.id).delete()
    db_session.commit()

    # Seed 28 days of baseline sales with mean ~20 units (std ~2.5)
    base_date = date(2026, 7, 1)
    for i in range(28):
        d = base_date + timedelta(days=i)
        # Alternate 18, 20, 22
        units = 20 + ((i % 3) - 1) * 2
        sale = Sales(
            product_id=prod.id,
            store_id=store.id,
            date=d,
            units_sold=units,
            revenue=units * 89.99,
        )
        db_session.add(sale)

    db_session.commit()
    return prod, store, base_date


def test_zscore_demand_spike_detection(db_session, anomaly_test_data):
    """
    Test that a 120-unit sale on day 29 (against baseline mean=20, std~1.6)
    triggers a critical spike alert with Z > 4.0.
    """
    prod, store, base_date = anomaly_test_data
    target_date = base_date + timedelta(days=28)

    # Insert demand spike
    spike_sale = Sales(
        product_id=prod.id,
        store_id=store.id,
        date=target_date,
        units_sold=120,
        revenue=120 * 89.99,
    )
    db_session.add(spike_sale)
    db_session.commit()

    service = AnomalyDetectionService(db_session)
    anomaly = service.detect_zscore_anomalies(
        product_id=prod.id,
        store_id=store.id,
        target_date=target_date,
    )

    assert anomaly is not None
    assert anomaly["type"] == "spike"
    assert anomaly["severity"] == "critical"
    assert anomaly["z_score"] >= 4.0
    assert "spiked" in anomaly["message"]
    assert "500%" in anomaly["message"] or "spiked" in anomaly["message"]


def test_zscore_demand_drop_detection(db_session, anomaly_test_data):
    """
    Test that a 0-unit sale on day 29 (against baseline mean=20, std~1.6)
    triggers a drop alert.
    """
    prod, store, base_date = anomaly_test_data
    target_date = base_date + timedelta(days=28)

    # Insert demand drop (0 units)
    drop_sale = Sales(
        product_id=prod.id,
        store_id=store.id,
        date=target_date,
        units_sold=0,
        revenue=0.0,
    )
    db_session.add(drop_sale)
    db_session.commit()

    service = AnomalyDetectionService(db_session)
    anomaly = service.detect_zscore_anomalies(
        product_id=prod.id,
        store_id=store.id,
        target_date=target_date,
    )

    assert anomaly is not None
    assert anomaly["type"] == "drop"
    assert anomaly["z_score"] >= 2.5
    assert "dropped" in anomaly["message"]


def test_24h_alert_deduplication(db_session, anomaly_test_data):
    """
    Test that calling create_or_update_alert twice within 24 hours updates
    the existing alert instead of creating a duplicate row.
    """
    prod, store, _ = anomaly_test_data
    service = AnomalyDetectionService(db_session)

    alert_data_1 = {
        "product_id": prod.id,
        "store_id": store.id,
        "type": "spike",
        "severity": "warning",
        "message": "Initial spike alert notification.",
    }

    # 1. First alert creation
    alert_1, is_new_1 = service.create_or_update_alert(alert_data_1)
    assert is_new_1 is True

    initial_id = alert_1.id
    count_after_1 = (
        db_session.query(Alert)
        .filter(Alert.product_id == prod.id, Alert.store_id == store.id, Alert.type == "spike")
        .count()
    )
    assert count_after_1 == 1

    # 2. Second alert within 24 hours with escalated severity
    alert_data_2 = {
        "product_id": prod.id,
        "store_id": store.id,
        "type": "spike",
        "severity": "critical",
        "message": "Updated critical spike alert notification.",
    }

    alert_2, is_new_2 = service.create_or_update_alert(alert_data_2)
    assert is_new_2 is False
    assert alert_2.id == initial_id
    assert alert_2.severity == "critical"
    assert "Updated critical spike" in alert_2.message

    # Total rows in DB should still be exactly 1
    total_alerts = (
        db_session.query(Alert)
        .filter(Alert.product_id == prod.id, Alert.store_id == store.id, Alert.type == "spike")
        .count()
    )
    assert total_alerts == 1


def test_stockout_risk_scan_alert_generation(db_session, anomaly_test_data):
    """
    Test that run_stockout_risk_scan creates an alert for critically understocked items.
    """
    prod, store, _ = anomaly_test_data
    service = AnomalyDetectionService(db_session)

    # Set inventory to critical stock (2 units)
    inv = db_session.query(Inventory).filter(Inventory.product_id == prod.id, Inventory.store_id == store.id).first()
    if not inv:
        inv = Inventory(product_id=prod.id, store_id=store.id, current_stock=2, reorder_point=40, safety_stock=20)
        db_session.add(inv)
    else:
        inv.current_stock = 2
        inv.reorder_point = 40
    db_session.commit()

    alerts = service.run_stockout_risk_scan()
    assert len(alerts) >= 1
    stockout_alert = next((a for a in alerts if a.product_id == prod.id and a.type == "stockout"), None)
    assert stockout_alert is not None
    assert stockout_alert.severity == "critical"
    assert "Stockout risk critical" in stockout_alert.message


def test_alert_config_endpoints(client, admin_token):
    """
    Test GET /api/alerts/config, POST /api/alerts/config, and POST /api/alerts/scan endpoints.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. GET Config
    get_res = client.get("/api/alerts/config", headers=headers)
    assert get_res.status_code == 200
    config_data = get_res.json()
    assert "z_score_threshold" in config_data
    assert "critical_z_threshold" in config_data

    # 2. POST Config Update
    new_config = {
        "z_score_threshold": 3.0,
        "critical_z_threshold": 4.5,
        "isolation_forest_contamination": 0.08,
        "high_risk_doc_days": 6.0,
        "medium_risk_doc_days": 12.0,
        "lookback_window_days": 30,
    }
    post_res = client.post("/api/alerts/config", json=new_config, headers=headers)
    assert post_res.status_code == 200
    assert post_res.json()["z_score_threshold"] == 3.0

    # 3. Trigger Anomaly Scan
    scan_res = client.post("/api/alerts/scan", headers=headers)
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["status"] == "completed"
    assert "sku_store_pairs_scanned" in scan_data

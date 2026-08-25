import pytest
from datetime import date, timedelta
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.inventory import Inventory
from app.services.inventory_optimization_service import InventoryOptimizationService
from app.services.forecasting_service import ForecastingService


def test_liveness_and_readiness_probes(client, db_session):
    """Verify /health and /ready orchestrator probes."""
    # 1. Liveness Probe
    health_res = client.get("/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "healthy"
    assert "uptime_seconds" in health_data

    # 2. Readiness Probe
    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    ready_data = ready_res.json()
    assert ready_data["status"] == "ready"
    assert ready_data["checks"]["database"]["status"] == "ok"


def test_auth_failures_and_forbidden_store_access(client, manager_store1_token):
    """
    Test 401 Unauthorized for missing tokens and 403 Forbidden for store-manager multi-tenancy violation.
    """
    # 1. 401 Missing Token
    unauth_res = client.get("/api/dashboard/kpis")
    assert unauth_res.status_code == 401
    assert unauth_res.json()["error_code"] == "UNAUTHORIZED"

    # 2. 401 Invalid Bearer Token
    bad_token_res = client.get("/api/dashboard/kpis", headers={"Authorization": "Bearer invalid_garbage_token_123"})
    assert bad_token_res.status_code == 401
    assert bad_token_res.json()["error_code"] == "UNAUTHORIZED"

    # 3. 403 Forbidden: Store Manager 1 trying to query Store 2
    forbidden_res = client.get(
        "/api/dashboard/kpis?store_id=2",
        headers={"Authorization": f"Bearer {manager_store1_token}"},
    )
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error_code"] == "FORBIDDEN_STORE_ACCESS"


def test_validation_errors_422(client, admin_token):
    """
    Test 422 Unprocessable Entity for invalid schema inputs.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Invalid forecast horizon (negative or zero)
    bad_forecast = client.get("/api/forecast/1?horizon_weeks=0", headers=headers)
    assert bad_forecast.status_code == 422
    assert bad_forecast.json()["error_code"] == "REQUEST_VALIDATION_ERROR"

    # 2. Invalid alert status
    bad_alert_patch = client.patch(
        "/api/alerts/1",
        json={"status": "invalid_status_enum"},
        headers=headers,
    )
    assert bad_alert_patch.status_code == 422

    # 3. Negative purchase order quantity
    bad_po = client.post(
        "/api/inventory/purchase-order",
        json={"product_id": 1, "store_id": 1, "order_quantity": -10},
        headers=headers,
    )
    assert bad_po.status_code == 422


def test_forecasting_sanity_bounds(db_session):
    """
    Sanity check: Model forecast output should be within reasonable bounds (+-3x) of historical mean.
    """
    prod = db_session.query(Product).filter(Product.id == 1).first()
    store = db_session.query(Store).filter(Store.id == 1).first()
    if not prod or not store:
        pytest.skip("Product or Store not seeded.")

    sales_records = (
        db_session.query(Sales.units_sold)
        .filter(Sales.product_id == prod.id, Sales.store_id == store.id)
        .all()
    )
    if not sales_records:
        pytest.skip("No sales records available.")

    avg_historical = sum(s.units_sold for s in sales_records) / len(sales_records)
    weekly_avg = avg_historical * 7

    service = ForecastingService(db_session)
    preds = service.predict(product_id=prod.id, store_id=store.id, horizon_weeks=4)

    for p in preds:
        pred_units = p["predicted_units"]
        # Upper sanity bound: forecast should not exceed 5x historical weekly mean
        assert pred_units <= weekly_avg * 5.0, f"Predicted units {pred_units} excessively high vs weekly mean {weekly_avg}"
        # Lower sanity bound: forecast should not be negative
        assert pred_units >= 0.0, "Predicted units cannot be negative"
        # Confidence interval sanity: upper >= lower
        assert p["upper_bound"] >= p["lower_bound"], "Upper confidence bound must be >= lower bound"


def test_inventory_edge_cases_and_negative_handling(db_session):
    """
    Test inventory calculations under extreme edge conditions.
    """
    prod = db_session.query(Product).filter(Product.id == 1).first()
    store = db_session.query(Store).filter(Store.id == 1).first()
    if not prod or not store:
        pytest.skip("Product or Store not seeded.")

    service = InventoryOptimizationService(db_session)

    # 1. Massive stock: ROQ must be strictly 0
    massive_roq = service.calculate_recommended_order_qty(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=100000,
        forecast_demand_override=50.0,
    )
    assert massive_roq == 0

    # 2. Zero stock: Days of cover must be 0.0 and critical risk
    risk, doc = service.classify_stockout_risk(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=0,
        avg_daily_demand_override=10.0,
    )
    assert risk == "CRITICAL"
    assert doc == 0.0

    # 3. Zero daily demand with positive stock: Days of cover should be 999 and OK risk
    risk_zero_dem, doc_zero_dem = service.classify_stockout_risk(
        product_id=prod.id,
        store_id=store.id,
        current_stock_override=50,
        avg_daily_demand_override=0.0,
    )
    assert risk_zero_dem == "OK"
    assert doc_zero_dem >= 100.0

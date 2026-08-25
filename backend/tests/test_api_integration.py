import pytest
from datetime import date, timedelta
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.inventory import Inventory
from app.models.alert import Alert
from app.models.purchase_order import PurchaseOrder


@pytest.fixture
def seed_inventory_and_alerts(db_session):
    """Seed inventory items and alerts for integration tests."""
    prod = db_session.query(Product).filter(Product.sku_code == "SKU-KEYBOARD").first()
    store1 = db_session.query(Store).filter(Store.id == 1).first()
    store2 = db_session.query(Store).filter(Store.id == 2).first()

    # Clear previous
    db_session.query(Inventory).filter(Inventory.product_id == prod.id).delete()
    db_session.query(Alert).delete()
    db_session.commit()

    # Inventory for Store 1 (Critical: 8 <= 20*0.5)
    inv1 = Inventory(
        product_id=prod.id,
        store_id=store1.id,
        current_stock=8,
        reorder_point=20,
        safety_stock=10,
    )
    # Inventory for Store 2 (OK: 45 > 20)
    inv2 = Inventory(
        product_id=prod.id,
        store_id=store2.id,
        current_stock=45,
        reorder_point=20,
        safety_stock=10,
    )
    db_session.add(inv1)
    db_session.add(inv2)

    # Seed an Alert
    alert = Alert(
        type="stockout",
        severity="critical",
        product_id=prod.id,
        store_id=store1.id,
        message="Stock level critically low in Seattle.",
        status="new",
    )
    db_session.add(alert)
    db_session.commit()
    return prod, store1, store2, alert


# 1. AUTHENTICATION & RBAC TESTS
def test_auth_register_and_login_flow(client, admin_token, planner_token, db_session):
    """Admin can register new users; non-admins get 403; users can login & refresh."""
    from app.models.user import User
    db_session.query(User).filter(User.email.in_(["new_planner@demandiq.io", "hacker@demandiq.io"])).delete()
    db_session.commit()

    # 1. Admin registers new planner
    reg_resp = client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "New Planner",
            "email": "new_planner@demandiq.io",
            "password": "strongpassword123",
            "role": "planner",
        },
    )
    assert reg_resp.status_code == 201
    assert reg_resp.json()["email"] == "new_planner@demandiq.io"

    # 2. Non-admin attempting to register gets 403 Forbidden
    forbidden_resp = client.post(
        "/api/auth/register",
        headers={"Authorization": f"Bearer {planner_token}"},
        json={
            "name": "Hacker User",
            "email": "hacker@demandiq.io",
            "password": "password123",
            "role": "admin",
        },
    )
    assert forbidden_resp.status_code == 403
    assert "error_code" in forbidden_resp.json()

    # 3. Login with registered user credentials
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "new_planner@demandiq.io", "password": "strongpassword123"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["user"]["email"] == "new_planner@demandiq.io"

    # 4. Exchange refresh token for new access token
    refresh_resp = client.post(
        "/api/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    # 5. Invalid credentials return 401
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "new_planner@demandiq.io", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["error_code"] == "UNAUTHORIZED"


# 2. STORE ISOLATION TESTS
def test_store_manager_store_isolation(client, manager_store1_token, seed_inventory_and_alerts):
    """Store manager can access their own store data, but accessing another store returns 403."""
    prod, store1, store2, _ = seed_inventory_and_alerts

    # Manager of Store 1 accessing Store 1 inventory -> 200 OK
    resp_ok = client.get(
        f"/api/inventory/recommendations?store_id=1",
        headers={"Authorization": f"Bearer {manager_store1_token}"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["total"] >= 1

    # Manager of Store 1 attempting to access Store 2 inventory -> 403 Forbidden
    resp_forbidden = client.get(
        f"/api/inventory/recommendations?store_id=2",
        headers={"Authorization": f"Bearer {manager_store1_token}"},
    )
    assert resp_forbidden.status_code == 403
    assert resp_forbidden.json()["error_code"] == "FORBIDDEN_STORE_ACCESS"

    # Manager of Store 1 attempting to create PO for Store 2 -> 403 Forbidden
    po_forbidden = client.post(
        "/api/inventory/purchase-order",
        headers={"Authorization": f"Bearer {manager_store1_token}"},
        json={
            "product_id": prod.id,
            "store_id": 2,
            "order_quantity": 50,
        },
    )
    assert po_forbidden.status_code == 403


# 3. FORECAST ENDPOINTS TESTS
def test_forecast_endpoints(client, planner_token, manager_store1_token, seed_inventory_and_alerts):
    prod, store1, _, _ = seed_inventory_and_alerts

    # 1. GET /api/forecast/{product_id}?store_id=1
    f_resp = client.get(
        f"/api/forecast/{prod.id}?store_id=1&horizon_weeks=4",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert f_resp.status_code == 200
    f_data = f_resp.json()
    assert len(f_data["predictions"]) == 4
    for p in f_data["predictions"]:
        assert p["lower_bound"] <= p["predicted_units"] <= p["upper_bound"]

    # 2. GET /api/forecast/accuracy
    acc_resp = client.get(
        f"/api/forecast/accuracy?product_id={prod.id}&store_id=1",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert acc_resp.status_code == 200
    assert "is_cold_start" in acc_resp.json()

    # 3. POST /api/forecast/retrain (Planner allowed)
    retrain_ok = client.post(
        "/api/forecast/retrain?horizon_weeks=2",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert retrain_ok.status_code == 200
    assert retrain_ok.json()["status"] == "completed"

    # 4. POST /api/forecast/retrain (Store manager forbidden)
    retrain_forbidden = client.post(
        "/api/forecast/retrain?horizon_weeks=2",
        headers={"Authorization": f"Bearer {manager_store1_token}"},
    )
    assert retrain_forbidden.status_code == 403


# 4. INVENTORY & PURCHASE ORDER TESTS
def test_inventory_and_purchase_order_flow(client, planner_token, seed_inventory_and_alerts):
    prod, store1, _, _ = seed_inventory_and_alerts

    # 1. GET /api/inventory/recommendations
    rec_resp = client.get(
        "/api/inventory/recommendations",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert rec_resp.status_code == 200
    data = rec_resp.json()
    assert "items" in data
    assert data["total"] >= 2
    # Verify risk levels present
    risk_levels = [item["risk_level"] for item in data["items"]]
    assert "CRITICAL" in risk_levels or "WARNING" in risk_levels or "OK" in risk_levels

    # 2. POST /api/inventory/purchase-order
    po_resp = client.post(
        "/api/inventory/purchase-order",
        headers={"Authorization": f"Bearer {planner_token}"},
        json={
            "product_id": prod.id,
            "store_id": store1.id,
            "order_quantity": 40,
            "supplier_name": "Logitech Global",
            "expected_delivery_date": str(date.today() + timedelta(days=5)),
        },
    )
    assert po_resp.status_code == 201
    po_data = po_resp.json()
    assert po_data["order_quantity"] == 40
    assert po_data["unit_cost"] == prod.unit_cost
    assert po_data["total_cost"] == round(40 * prod.unit_cost, 2)
    assert po_data["status"] == "submitted"


# 5. ALERTS MANAGEMENT TESTS
def test_alerts_filtering_and_patching(client, planner_token, seed_inventory_and_alerts):
    _, _, _, alert = seed_inventory_and_alerts

    # 1. GET /api/alerts with filters
    alerts_resp = client.get(
        "/api/alerts?severity=critical&status=new",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert alerts_resp.status_code == 200
    assert alerts_resp.json()["total"] >= 1

    # 2. PATCH /api/alerts/{id} to acknowledge
    patch_resp = client.patch(
        f"/api/alerts/{alert.id}",
        headers={"Authorization": f"Bearer {planner_token}"},
        json={"status": "acknowledged"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "acknowledged"


# 6. REPORTS & PROMOTION SIMULATION TESTS
def test_reports_and_simulation(client, planner_token, seed_inventory_and_alerts):
    prod, _, _, _ = seed_inventory_and_alerts

    # 1. GET /api/reports
    reports_resp = client.get(
        "/api/reports",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert reports_resp.status_code == 200
    assert reports_resp.json()["total"] >= 1

    # 2. POST /api/reports/export (CSV format)
    csv_resp = client.post(
        "/api/reports/export?type=demand_summary&format=csv",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "product_id" in csv_resp.text

    # 3. POST /api/reports/export (PDF format)
    pdf_resp = client.post(
        "/api/reports/export?type=accuracy_evaluation&format=pdf",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.headers["content-type"]

    # 4. POST /api/simulate (What-If Promotional uplift curve)
    sim_resp = client.post(
        "/api/simulate",
        headers={"Authorization": f"Bearer {planner_token}"},
        json={
            "product_id": prod.id,
            "discount_pct": 25.0,
            "promo_duration_days": 14,
        },
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["discount_pct"] == 25.0
    assert sim_data["total_unit_uplift"] > 0
    assert len(sim_data["curve"]) == 14


# 7. DASHBOARD KPIS TESTS
def test_dashboard_kpis(client, planner_token):
    kpis_resp = client.get(
        "/api/dashboard/kpis",
        headers={"Authorization": f"Bearer {planner_token}"},
    )
    assert kpis_resp.status_code == 200
    kpis = kpis_resp.json()
    assert "projected_revenue_30d" in kpis
    assert "overall_accuracy_pct" in kpis
    assert "stockout_risk_count" in kpis
    assert kpis["total_active_products"] >= 1

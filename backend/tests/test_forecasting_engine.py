import os
import pytest
from datetime import date, timedelta
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.promotion import Promotion
from app.models.forecast import ForecastResult
from app.services.forecasting_service import ForecastingService
from app.ml.storage import ModelStorage


@pytest.fixture
def seeded_ml_db(db_session):
    """Seed product, store, and 70 days of synthetic sales history."""
    # 1. Product with mature history (>8 weeks = 70 days)
    prod = db_session.query(Product).filter(Product.sku_code == "SKU-KEYBOARD").first()
    if not prod:
        prod = Product(
            sku_code="SKU-KEYBOARD",
            name="Ergonomic Keyboard",
            category="Electronics",
            subcategory="Peripherals",
            unit_price=89.99,
            unit_cost=45.00,
            lead_time_days=5,
        )
        db_session.add(prod)
        db_session.commit()

    # 2. Store
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

    # 3. New Product for Cold Start testing (<8 weeks history = 10 days)
    new_prod = db_session.query(Product).filter(Product.sku_code == "SKU-NEW-HEADSET").first()
    if not new_prod:
        new_prod = Product(
            sku_code="SKU-NEW-HEADSET",
            name="Brand New Wireless Headset",
            category="Electronics",
            subcategory="Audio",
            unit_price=149.99,
            unit_cost=75.00,
            lead_time_days=7,
        )
        db_session.add(new_prod)
        db_session.commit()

    # Clear existing sales for these test products
    db_session.query(Sales).filter(Sales.product_id.in_([prod.id, new_prod.id])).delete()
    db_session.commit()

    # Seed 70 days of history for mature product (SKU-KEYBOARD)
    start_date = date(2026, 6, 1)
    for i in range(70):
        cur_date = start_date + timedelta(days=i)
        dow = cur_date.weekday()
        # Realistic pattern: base 20, weekend spike +10, slight upward trend
        units = 20 + (10 if dow in [5, 6] else 0) + (i // 10)
        s = Sales(
            product_id=prod.id,
            store_id=store.id,
            date=cur_date,
            units_sold=units,
            revenue=round(units * prod.unit_price, 2),
            promotion_id=None,
        )
        db_session.add(s)

    # Seed only 10 days of history for cold-start product (SKU-NEW-HEADSET)
    cold_start_date = date(2026, 8, 1)
    for i in range(10):
        cur_date = cold_start_date + timedelta(days=i)
        s = Sales(
            product_id=new_prod.id,
            store_id=store.id,
            date=cur_date,
            units_sold=8,
            revenue=round(8 * new_prod.unit_price, 2),
            promotion_id=None,
        )
        db_session.add(s)

    db_session.commit()
    return prod, new_prod, store


def test_forecast_output_shape(db_session, seeded_ml_db):
    """Verify forecast returns exactly N horizon weeks."""
    prod, _, store = seeded_ml_db
    service = ForecastingService(db_session)

    # 4 weeks
    preds_4w = service.predict(product_id=prod.id, store_id=store.id, horizon_weeks=4)
    assert len(preds_4w) == 4
    for idx, p in enumerate(preds_4w):
        assert p["week_index"] == idx + 1
        assert "forecast_date" in p
        assert "predicted_units" in p

    # 8 weeks
    preds_8w = service.predict(product_id=prod.id, store_id=store.id, horizon_weeks=8)
    assert len(preds_8w) == 8


def test_confidence_interval_ordering(db_session, seeded_ml_db):
    """Verify lower_bound <= predicted_units <= upper_bound across all models."""
    prod, _, store = seeded_ml_db
    service = ForecastingService(db_session)

    for model_type in ["prophet", "xgboost", "ensemble"]:
        preds = service.predict(
            product_id=prod.id,
            store_id=store.id,
            horizon_weeks=4,
            model_type=model_type,
        )
        assert len(preds) == 4
        for p in preds:
            lower = p["lower_bound"]
            pred = p["predicted_units"]
            upper = p["upper_bound"]

            assert lower >= 0.0, f"Lower bound should be non-negative: {lower}"
            assert lower <= pred, f"Invariant violated: lower ({lower}) > predicted ({pred})"
            assert pred <= upper, f"Invariant violated: predicted ({pred}) > upper ({upper})"


def test_cold_start_fallback_triggering(db_session, seeded_ml_db):
    """Verify products with <8 weeks of history trigger category average fallback."""
    _, new_prod, store = seeded_ml_db
    service = ForecastingService(db_session)

    preds = service.predict(product_id=new_prod.id, store_id=store.id, horizon_weeks=4)
    assert len(preds) == 4

    for p in preds:
        assert p["is_cold_start"] is True
        assert p["confidence_level"] == "low"
        assert p["model_used"] == "category_average_fallback"
        assert p["lower_bound"] <= p["predicted_units"] <= p["upper_bound"]
        assert p["predicted_units"] > 0


def test_model_training_and_artifact_storage(db_session, seeded_ml_db, tmp_path):
    """Verify model training and joblib artifact serialization on disk."""
    prod, _, store = seeded_ml_db
    storage = ModelStorage(base_dir=str(tmp_path))
    service = ForecastingService(db_session, storage=storage)

    res = service.train(
        product_id=prod.id,
        store_id=store.id,
        model_type="ensemble",
        version="2.0",
    )

    assert res["status"] == "trained"
    assert res["version"] == "2.0"
    assert "metrics" in res
    assert os.path.exists(res["artifact_path"])
    assert storage.has_model(prod.id, store.id, "ensemble")

    loaded = storage.load_model(prod.id, store.id, "ensemble", version="2.0")
    assert loaded is not None
    assert loaded["version"] == "2.0"
    assert loaded["product_id"] == prod.id


def test_model_evaluation_metrics(db_session, seeded_ml_db):
    """Verify evaluation returns valid MAPE, RMSE, and ensemble weights."""
    prod, _, store = seeded_ml_db
    service = ForecastingService(db_session)

    eval_res = service.evaluate(product_id=prod.id, store_id=store.id, validation_weeks=2)
    assert eval_res["is_cold_start"] is False
    assert "ensemble_metrics" in eval_res
    assert eval_res["ensemble_metrics"]["mape"] >= 0.0
    assert eval_res["ensemble_metrics"]["rmse"] >= 0.0
    assert (
        pytest.approx(eval_res["prophet_weight"] + eval_res["xgboost_weight"], 0.01)
        == 1.0
    )


def test_scheduled_retrain_all_skus(db_session, seeded_ml_db):
    """Verify batch retraining job iterates SKU-store pairs and persists to ForecastResult."""
    service = ForecastingService(db_session)

    retrain_res = service.retrain_all_active_skus(horizon_weeks=4)
    assert retrain_res["status"] == "completed"
    assert retrain_res["forecast_results_created"] > 0

    # Verify rows written to ForecastResult database table
    db_results = db_session.query(ForecastResult).all()
    assert len(db_results) > 0
    for f in db_results:
        assert f.lower_bound <= f.predicted_units <= f.upper_bound
        assert f.model_used is not None


def test_forecasting_api_endpoints(client, seeded_ml_db, planner_token):
    """Verify FastAPI route handlers for training, predicting, and evaluating."""
    prod, new_prod, store = seeded_ml_db
    headers = {"Authorization": f"Bearer {planner_token}"}

    # 1. Train endpoint
    train_resp = client.post(
        "/api/v1/forecast/train",
        headers=headers,
        json={
            "product_id": prod.id,
            "store_id": store.id,
            "model_type": "ensemble",
            "version": "1.0",
        },
    )
    assert train_resp.status_code == 200
    assert train_resp.json()["status"] in ["trained", "cold_start_active"]

    # 2. Predict endpoint
    predict_resp = client.get(
        f"/api/v1/forecast/{prod.id}?store_id={store.id}&horizon_weeks=4&model_type=ensemble",
        headers=headers,
    )
    assert predict_resp.status_code == 200
    p_data = predict_resp.json()
    assert len(p_data["predictions"]) == 4

    # 3. Evaluate endpoint
    eval_resp = client.get(
        f"/api/v1/forecast/accuracy?product_id={prod.id}&store_id={store.id}&validation_weeks=2",
        headers=headers,
    )
    assert eval_resp.status_code == 200
    assert "ensemble_metrics" in eval_resp.json() or "mape" in eval_resp.json()

    # 4. Retrain-all endpoint
    retrain_resp = client.post(
        "/api/v1/forecast/retrain?horizon_weeks=4",
        headers=headers,
    )
    assert retrain_resp.status_code == 200
    assert retrain_resp.json()["status"] == "completed"


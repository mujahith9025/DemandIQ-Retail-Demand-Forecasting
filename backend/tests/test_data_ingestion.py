import io
import pytest
from datetime import date
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.sales_summary import WeeklySalesSummary
from app.services.aggregation_service import aggregate_weekly_sales_sync


def test_valid_sales_upload(client, db_session):
    """Test successful CSV upload with bulk insertion and automatic weekly aggregation."""
    # Clean previous sales
    db_session.query(Sales).delete()
    db_session.query(WeeklySalesSummary).delete()
    db_session.commit()

    csv_content = (
        "date,sku_code,store_id,units_sold,revenue\n"
        "2026-08-17,SKU-KEYBOARD,1,10,899.90\n"
        "2026-08-18,SKU-KEYBOARD,1,15,1349.85\n"
        "2026-08-19,SKU-MONITOR,2,5,1499.95\n"
    )

    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("sales_history.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["total_rows"] == 3
    assert data["inserted_rows"] == 3
    assert data["date_range"]["start_date"] == "2026-08-17"
    assert data["date_range"]["end_date"] == "2026-08-19"
    assert data["background_job_triggered"] is True

    # Verify rows in database
    sales_count = db_session.query(Sales).count()
    assert sales_count == 3

    # Run and test aggregation
    updated_summaries = aggregate_weekly_sales_sync(db=db_session)
    assert updated_summaries >= 2

    # Check weekly summary values for SKU-KEYBOARD in Store 1 (10 + 15 = 25 units, revenue = 2249.75)
    prod = db_session.query(Product).filter(Product.sku_code == "SKU-KEYBOARD").first()
    summary = (
        db_session.query(WeeklySalesSummary)
        .filter(
            WeeklySalesSummary.product_id == prod.id,
            WeeklySalesSummary.store_id == 1,
            WeeklySalesSummary.year == 2026,
        )
        .first()
    )
    assert summary is not None
    assert summary.total_units_sold == 25
    assert summary.total_revenue == pytest.approx(2249.75, 0.01)


def test_missing_column_rejection(client, db_session):
    """Test rejection when required column is missing."""
    csv_missing_col = (
        "date,sku_code,store_id,units_sold\n"  # missing 'revenue'
        "2026-08-20,SKU-KEYBOARD,1,10\n"
    )

    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("invalid.csv", io.BytesIO(csv_missing_col.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "validation_error"
    assert any("revenue" in err["issue"] for err in data["errors"])


def test_duplicate_row_in_file_rejection(client, db_session):
    """Test rejection when duplicate (sku, store, date) is present in the uploaded file."""
    initial_sales_count = db_session.query(Sales).count()

    csv_duplicates = (
        "date,sku_code,store_id,units_sold,revenue\n"
        "2026-08-22,SKU-KEYBOARD,1,10,899.90\n"
        "2026-08-22,SKU-KEYBOARD,1,15,1349.85\n"  # duplicate key
    )

    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("duplicates.csv", io.BytesIO(csv_duplicates.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "validation_error"
    assert any("Duplicate record in uploaded file" in err["issue"] for err in data["errors"])

    # Ensure atomic rollback (zero rows inserted)
    assert db_session.query(Sales).count() == initial_sales_count


def test_duplicate_row_against_db_rejection(client, db_session):
    """Test rejection when row already exists in database."""
    prod = db_session.query(Product).filter(Product.sku_code == "SKU-KEYBOARD").first()
    target_date = date(2026, 8, 17)
    existing_sale = (
        db_session.query(Sales)
        .filter(Sales.product_id == prod.id, Sales.store_id == 1, Sales.date == target_date)
        .first()
    )
    assert existing_sale is not None

    csv_existing = (
        "date,sku_code,store_id,units_sold,revenue\n"
        "2026-08-17,SKU-KEYBOARD,1,20,1799.80\n"
    )

    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("existing.csv", io.BytesIO(csv_existing.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "validation_error"
    assert any("already exists in database" in err["issue"] for err in data["errors"])


def test_unknown_sku_rejection(client, db_session):
    """Test rejection when SKU is not in the Product database."""
    csv_unknown_sku = (
        "date,sku_code,store_id,units_sold,revenue\n"
        "2026-08-25,SKU-NON-EXISTENT-999,1,10,500.00\n"
    )

    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("unknown_sku.csv", io.BytesIO(csv_unknown_sku.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "validation_error"
    assert any("Unknown SKU code" in err["issue"] for err in data["errors"])
    assert data["errors"][0]["row_number"] == 2


def test_unknown_store_rejection(client, db_session):
    """Test rejection when Store ID is not in the Store database."""
    csv_unknown_store = (
        "date,sku_code,store_id,units_sold,revenue\n"
        "2026-08-25,SKU-KEYBOARD,9999,10,899.90\n"
    )

    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("unknown_store.csv", io.BytesIO(csv_unknown_store.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "validation_error"
    assert any("Unknown store ID" in err["issue"] for err in data["errors"])


def test_negative_units_sold_rejection(client, db_session):
    """Test rejection when units_sold is negative."""
    csv_negative_units = (
        "date,sku_code,store_id,units_sold,revenue\n"
        "2026-08-25,SKU-KEYBOARD,1,-5,100.00\n"
    )

    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("negative_units.csv", io.BytesIO(csv_negative_units.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "validation_error"
    assert any("Negative units sold" in err["issue"] for err in data["errors"])


def test_root_alias_upload(client, db_session):
    """Test that the /api/data/upload root alias endpoint works identically."""
    csv_content = (
        "date,sku_code,store_id,units_sold,revenue\n"
        "2026-08-24,SKU-MONITOR,2,8,2399.92\n"
    )

    response = client.post(
        "/api/data/upload",
        files={"file": ("sales_alias.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["inserted_rows"] == 1

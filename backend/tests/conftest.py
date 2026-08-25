import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.product import Product
from app.models.store import Store
from app.models.sales import Sales
from app.models.inventory import Inventory
from app.models.alert import Alert
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Yield a database session and clean up sales between test cases."""
    session = SessionLocal()
    try:
        # Seed test Product & Store if not present
        if not session.query(Product).filter(Product.sku_code == "SKU-KEYBOARD").first():
            p1 = Product(
                sku_code="SKU-KEYBOARD",
                name="Ergonomic Keyboard",
                category="Electronics",
                subcategory="Peripherals",
                unit_price=89.99,
                unit_cost=45.00,
                lead_time_days=5,
            )
            session.add(p1)

        if not session.query(Product).filter(Product.sku_code == "SKU-MONITOR").first():
            p2 = Product(
                sku_code="SKU-MONITOR",
                name="4K Monitor",
                category="Electronics",
                subcategory="Displays",
                unit_price=299.99,
                unit_cost=180.00,
                lead_time_days=7,
            )
            session.add(p2)

        if not session.query(Store).filter(Store.id == 1).first():
            s1 = Store(
                id=1,
                name="Downtown Flagship",
                location="100 Main St",
                city="Seattle",
                region="Pacific Northwest",
                timezone="America/Los_Angeles",
            )
            session.add(s1)

        if not session.query(Store).filter(Store.id == 2).first():
            s2 = Store(
                id=2,
                name="Metro Hub",
                location="500 Broadway",
                city="New York",
                region="Northeast",
                timezone="America/New_York",
            )
            session.add(s2)

        # Seed Users
        if not session.query(User).filter(User.email == "admin@demandiq.io").first():
            admin_user = User(
                name="Admin User",
                email="admin@demandiq.io",
                hashed_password=get_password_hash("adminpassword123"),
                role="admin",
                assigned_store_id=None,
            )
            session.add(admin_user)

        if not session.query(User).filter(User.email == "planner@demandiq.io").first():
            planner_user = User(
                name="Supply Planner",
                email="planner@demandiq.io",
                hashed_password=get_password_hash("plannerpassword123"),
                role="planner",
                assigned_store_id=None,
            )
            session.add(planner_user)

        if not session.query(User).filter(User.email == "manager_store1@demandiq.io").first():
            mgr1 = User(
                name="Store 1 Manager",
                email="manager_store1@demandiq.io",
                hashed_password=get_password_hash("managerpassword123"),
                role="store_manager",
                assigned_store_id=1,
            )
            session.add(mgr1)

        if not session.query(User).filter(User.email == "manager_store2@demandiq.io").first():
            mgr2 = User(
                name="Store 2 Manager",
                email="manager_store2@demandiq.io",
                hashed_password=get_password_hash("managerpassword123"),
                role="store_manager",
                assigned_store_id=2,
            )
            session.add(mgr2)

        session.commit()
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(db_session):
    user = db_session.query(User).filter(User.email == "admin@demandiq.io").first()
    return create_access_token(user_id=user.id, email=user.email, role=user.role, assigned_store_id=user.assigned_store_id)


@pytest.fixture
def planner_token(db_session):
    user = db_session.query(User).filter(User.email == "planner@demandiq.io").first()
    return create_access_token(user_id=user.id, email=user.email, role=user.role, assigned_store_id=user.assigned_store_id)


@pytest.fixture
def manager_store1_token(db_session):
    user = db_session.query(User).filter(User.email == "manager_store1@demandiq.io").first()
    return create_access_token(user_id=user.id, email=user.email, role=user.role, assigned_store_id=user.assigned_store_id)


@pytest.fixture
def manager_store2_token(db_session):
    user = db_session.query(User).filter(User.email == "manager_store2@demandiq.io").first()
    return create_access_token(user_id=user.id, email=user.email, role=user.role, assigned_store_id=user.assigned_store_id)

from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku_code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    subcategory = Column(String(100), nullable=True)
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    lead_time_days = Column(Integer, default=7, nullable=False)

    # Relationships
    sales = relationship("Sales", back_populates="product", cascade="all, delete-orphan")
    inventories = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    promotions = relationship("Promotion", back_populates="product")
    forecasts = relationship("ForecastResult", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product")
    weekly_summaries = relationship("WeeklySalesSummary", back_populates="product", cascade="all, delete-orphan")

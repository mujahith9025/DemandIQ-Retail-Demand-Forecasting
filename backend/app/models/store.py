from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Store(Base, TimestampMixin):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Relationships
    sales = relationship("Sales", back_populates="store", cascade="all, delete-orphan")
    inventories = relationship("Inventory", back_populates="store", cascade="all, delete-orphan")
    forecasts = relationship("ForecastResult", back_populates="store", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="store")
    assigned_users = relationship("User", back_populates="assigned_store")
    weekly_summaries = relationship("WeeklySalesSummary", back_populates="store", cascade="all, delete-orphan")

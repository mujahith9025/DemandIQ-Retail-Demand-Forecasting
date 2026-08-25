from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class ForecastResult(Base, TimestampMixin):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False, index=True)
    predicted_units = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    model_used = Column(String(50), default="lightgbm", nullable=False)
    mape = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    generated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_forecast_prod_store_date", "product_id", "store_id", "forecast_date"),
    )

    # Relationships
    product = relationship("Product", back_populates="forecasts")
    store = relationship("Store", back_populates="forecasts")

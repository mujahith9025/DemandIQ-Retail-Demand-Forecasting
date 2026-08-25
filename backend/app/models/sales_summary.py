from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class WeeklySalesSummary(Base):
    __tablename__ = "weekly_sales_summaries"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    week_number = Column(Integer, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_units_sold = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Float, default=0.0, nullable=False)
    last_aggregated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("product_id", "store_id", "year", "week_number", name="uq_weekly_summary_item"),
        Index("ix_weekly_summary_store_prod_year_week", "store_id", "product_id", "year", "week_number"),
    )

    # Relationships
    product = relationship("Product", back_populates="weekly_summaries")
    store = relationship("Store", back_populates="weekly_summaries")

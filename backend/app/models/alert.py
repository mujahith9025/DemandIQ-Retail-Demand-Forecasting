from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), index=True, nullable=False)  # spike, drop, stockout
    severity = Column(String(20), index=True, nullable=False)  # critical, warning, info
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=True, index=True)
    message = Column(Text, nullable=False)
    status = Column(String(30), default="new", index=True, nullable=False)  # new, acknowledged, dismissed
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_alerts_status_severity", "status", "severity"),
    )

    # Relationships
    product = relationship("Product", back_populates="alerts")
    store = relationship("Store", back_populates="alerts")

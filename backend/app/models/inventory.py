from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Inventory(Base, TimestampMixin):
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    current_stock = Column(Integer, default=0, nullable=False)
    reorder_point = Column(Integer, default=20, nullable=False)
    safety_stock = Column(Integer, default=10, nullable=False)
    last_updated = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("product_id", "store_id", name="uq_inventory_product_store"),
    )

    # Relationships
    product = relationship("Product", back_populates="inventories")
    store = relationship("Store", back_populates="inventories")

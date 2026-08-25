from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    order_quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    status = Column(String(30), default="submitted", index=True, nullable=False)  # draft, submitted, received, cancelled
    supplier_name = Column(String(255), default="Default Supplier", nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index("ix_po_store_product_status", "store_id", "product_id", "status"),
    )

    # Relationships
    product = relationship("Product")
    store = relationship("Store")
    created_by = relationship("User")

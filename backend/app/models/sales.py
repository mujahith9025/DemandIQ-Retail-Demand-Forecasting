from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Sales(Base, TimestampMixin):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    units_sold = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)
    promotion_id = Column(Integer, ForeignKey("promotions.id", ondelete="SET NULL"), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("product_id", "store_id", "date", name="uq_sales_product_store_date"),
        Index("ix_sales_store_product_date", "store_id", "product_id", "date"),
    )

    # Relationships
    product = relationship("Product", back_populates="sales")
    store = relationship("Store", back_populates="sales")
    promotion = relationship("Promotion", back_populates="sales")

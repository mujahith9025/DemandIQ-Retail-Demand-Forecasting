from sqlalchemy import Column, Integer, String, JSON
from app.core.database import Base
from app.models.base import TimestampMixin


class ReportRecord(Base, TimestampMixin):
    __tablename__ = "report_records"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), index=True, nullable=False)  # demand_summary, accuracy_evaluation, inventory_health
    format = Column(String(20), default="csv", nullable=False)  # csv, pdf
    status = Column(String(30), default="completed", nullable=False)  # completed, generating
    summary_metrics = Column(JSON, nullable=True)

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.alert import Alert


class AlertService:
    """Business logic for detecting inventory anomalies and stockout risks."""

    def __init__(self, db: Session):
        self.db = db

    def get_alerts(
        self,
        severity: Optional[str] = None,
        is_resolved: Optional[bool] = False,
        limit: int = 50,
    ) -> List[Alert]:
        query = self.db.query(Alert)
        if severity:
            query = query.filter(Alert.severity == severity)
        if is_resolved is not None:
            query = query.filter(Alert.is_resolved == is_resolved)
        return query.order_by(Alert.created_at.desc()).limit(limit).all()

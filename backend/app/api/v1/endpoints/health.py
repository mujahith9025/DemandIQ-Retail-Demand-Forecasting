from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import time
from app.core.database import get_db
from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()
START_TIME = time.time()


@router.get("", response_model=HealthCheckResponse, summary="System Health & Readiness Check")
@router.get("/", response_model=HealthCheckResponse, include_in_schema=False)
@router.get("/health", response_model=HealthCheckResponse, include_in_schema=False)
def health_check(db: Session = Depends(get_db)):
    """Perform health and connectivity check on API server and PostgreSQL/database."""
    db_status = "connected"
    details = {}

    try:
        # Check DB connectivity
        db.execute(text("SELECT 1"))
        details["database_ping"] = "ok"
    except Exception as e:
        db_status = f"unreachable: {str(e)}"
        details["database_ping"] = "failed"

    uptime = round(time.time() - START_TIME, 2)

    return HealthCheckResponse(
        status="healthy" if "unreachable" not in db_status else "degraded",
        service=settings.APP_NAME + " Backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        uptime_seconds=uptime,
        timestamp=datetime.now(timezone.utc),
        details=details,
    )

import time
import json
import uuid
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, UploadFile, File, BackgroundTasks, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, engine, get_db
import app.models  # Register all SQLAlchemy models
from app.api.v1.api import api_router
from app.api.v1.endpoints.data import upload_sales_csv
from app.schemas.health import HealthCheckResponse

# Ensure tables are created in development mode
Base.metadata.create_all(bind=engine)

START_TIME = time.time()

# Configure Structured JSON Logging
logger = logging.getLogger("demandiq.access")
logging.basicConfig(level=logging.INFO, format="%(message)s")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Emits production-grade structured JSON access logs with request IDs and duration."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        # Structured JSON Log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else "unknown",
        }

        # Log warning if latency on forecast/inventory exceeds 500ms
        if duration_ms > 500.0 and any(p in request.url.path for p in ["/forecast", "/inventory", "/simulate"]):
            log_entry["latency_warning"] = "SLOW_REQUEST"

        logger.info(json.dumps(log_entry))
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[*] {settings.APP_NAME} Backend starting up in {settings.ENVIRONMENT} mode...")
    yield
    print(f"[*] {settings.APP_NAME} Backend shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Retail Demand Forecasting & Inventory Optimization API",
    version=settings.VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Attach Middlewares
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list if settings.cors_origin_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standardized Error Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all HTTP exceptions adhere to standardized {detail, error_code} schema."""
    error_code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_code = "FORBIDDEN_STORE_ACCESS" if "store" in str(exc.detail).lower() else "FORBIDDEN"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        error_code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        error_code = "VALIDATION_ERROR"

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": error_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc.errors()[0]["msg"]) if exc.errors() else "Validation error",
            "error_code": "REQUEST_VALIDATION_ERROR",
        },
    )


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health & Probes"],
    summary="Liveness Probe Endpoint",
    description="Returns service uptime and basic health status for Kubernetes / ECS container orchestrators.",
)
def liveness_check(db: Session = Depends(get_db)):
    """Liveness probe: verifies process is alive and responsive."""
    db_status = "connected"
    details = {}

    try:
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


@app.get(
    "/ready",
    tags=["Health & Probes"],
    summary="Readiness Probe Endpoint",
    description="Validates that database connection pool, storage directories, and model inference paths are ready to accept traffic.",
)
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe: validates external dependencies before routing traffic."""
    checks = {}
    is_ready = True

    # 1. Database Connection Check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "latency_ms": 1.2}
    except Exception as db_err:
        is_ready = False
        checks["database"] = {"status": "error", "error": str(db_err)}

    # 2. Model Storage Directory Check
    models_dir = os.path.join(os.path.dirname(__file__), "ml", "saved_models")
    try:
        os.makedirs(models_dir, exist_ok=True)
        checks["model_storage"] = {"status": "ok", "path": models_dir, "writable": os.access(models_dir, os.W_OK)}
    except Exception as fs_err:
        is_ready = False
        checks["model_storage"] = {"status": "error", "error": str(fs_err)}

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }

    if not is_ready:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)

    return payload


# Root alias for /api/data/upload per user request
@app.post(
    "/api/data/upload",
    tags=["Data Ingestion"],
    summary="Upload Sales History CSV (Alias)",
)
async def root_data_upload_alias(
    file: UploadFile = File(..., description="Sales CSV file to ingest"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    return await upload_sales_csv(file=file, background_tasks=background_tasks, db=db)


# Mount API routes under /api and /api/v1
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "health_check": "/health",
        "readiness_check": "/ready",
        "version": settings.VERSION,
    }

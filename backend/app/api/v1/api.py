from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    data,
    forecast,
    inventory,
    alerts,
    reports,
    auth,
    dashboard,
    simulation,
)

api_router = APIRouter()

# Register core route modules
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(forecast.router, prefix="/forecast", tags=["Demand Forecasting"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory Management"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts & Anomalies"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Analytics"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Executive Dashboard"])
api_router.include_router(simulation.router, prefix="", tags=["Promotion Simulation"])
api_router.include_router(data.router, prefix="/data", tags=["Data Ingestion"])

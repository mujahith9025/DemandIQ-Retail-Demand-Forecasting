from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class HealthCheckResponse(BaseModel):
    status: str = Field(default="healthy", description="Overall health state: healthy | degraded | unhealthy")
    service: str = Field(default="DemandIQ Backend", description="Name of the service")
    version: str = Field(default="1.0.0", description="Semantic service version")
    environment: str = Field(default="development", description="Current environment (development, staging, production)")
    database: str = Field(default="connected", description="Database connection health state")
    uptime_seconds: Optional[float] = Field(default=None, description="Service uptime in seconds")
    timestamp: datetime = Field(description="Current UTC timestamp of response")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Diagnostic metadata")

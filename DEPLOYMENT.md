# DemandIQ Production Deployment & Operations Guide

This guide provides end-to-end procedures for deploying, maintaining, migrating, and operating **DemandIQ** in staging and production environments.

---

## 🏛️ 1. Production Architecture Overview

- **Backend Service**: FastAPI running under **Gunicorn** process manager with **4 asynchronous Uvicorn workers** running as non-root user `appuser` (UID 10001).
- **Frontend Service**: Next.js 14 App Router optimized in **Standalone output mode** running on minimal Alpine runtime.
- **Database**: PostgreSQL 15+ with connection pooling and automated Alembic schema migrations.
- **ML Storage**: Persistent storage volume mounted at `/app/app/ml/saved_models` for serialized Prophet and XGBoost joblib artifacts.
- **Observability**: Structured JSON access logs with request IDs, response times, and orchestrator probes (`/health`, `/ready`).

---

## 🚀 2. Production Database Migrations (Alembic)

Database schema updates must be executed prior to switching traffic to new container versions.

### Running Migrations in Production:
```bash
# 1. Access the production container or run via migration job
docker exec -it demandiq_backend_prod alembic upgrade head

# Or run directly against the production PostgreSQL instance:
DATABASE_URL="postgresql://demandiq_admin:SECRET@db.internal:5432/demandiq_production" alembic upgrade head
```

### Creating New Migrations:
```bash
# Generate auto-migration script after model changes
alembic revision --autogenerate -m "Add new inventory constraint"

# Review generated script in backend/alembic/versions/
```

---

## 🤖 3. Bootstrapping Initial ML Model Training

When deploying to a new environment with fresh sales data, bootstrap the forecasting models and inventory safety stock:

### Step 1: Ingest Initial Historical Sales Dataset
```bash
# Upload historical sales CSV (minimum 8 weeks history per SKU)
curl -X POST "https://api.demandiq.io/api/data/upload" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -F "file=@sales_history_2026.csv"
```

### Step 2: Trigger Batch Model Retraining
```bash
# Trains Prophet + XGBoost ensembles and computes holdout validation MAPEs
curl -X POST "https://api.demandiq.io/api/forecast/retrain?horizon_weeks=4" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

### Step 3: Run Initial Anomaly & Stockout Scan
```bash
curl -X POST "https://api.demandiq.io/api/alerts/scan" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

---

## 🩺 4. Health & Readiness Probes

### Liveness Probe (`GET /health`)
- **Purpose**: Verifies that the FastAPI process is alive and responsive.
- **Response**: HTTP 200 OK with uptime and database ping status.
- **Orchestrator Action**: If it fails 3 consecutive times, restart container.

```bash
curl -f http://localhost:8000/health
```

### Readiness Probe (`GET /ready`)
- **Purpose**: Validates database connection pool and model artifact directory write permissions before routing live user traffic.
- **Response**:
  - `HTTP 200 OK` (Ready for traffic)
  - `HTTP 503 Service Unavailable` (Database unreachable or storage unmounted)

```bash
curl -f http://localhost:8000/ready
```

---

## 🔄 5. Zero-Downtime Rollback Protocols

If a production release exhibits regressions or fails readiness probes:

### Scenario A: Blue/Green or Rolling Deployment Rollback
```bash
# 1. Revert container image tag to previous stable commit SHA in deployment manifest
docker service update --image ghcr.io/org/demandiq-backend:v1.0.4 demandiq_backend

# 2. Verify readiness
curl -f https://api.demandiq.io/ready
```

### Scenario B: Database Schema Downgrade (if necessary)
```bash
# Downgrade 1 revision
alembic downgrade -1
```

---

## 🐳 6. Local Production Emulation

To test production container builds and networking locally:

```bash
# Start production containers (Gunicorn + Standalone Next.js)
docker compose --profile prod up --build

# Verify running services
docker ps
curl http://localhost:8000/ready
curl http://localhost:3000/
```

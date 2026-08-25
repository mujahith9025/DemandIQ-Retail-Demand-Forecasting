# DemandIQ — Intelligent Retail Demand Forecasting

DemandIQ is an enterprise-grade AI-powered retail demand forecasting and inventory optimization platform. It combines machine learning models with real-time inventory telemetry to minimize stockouts, reduce carrying costs, and generate accurate replenishment signals.

---

## 🏗️ Architecture Overview

The repository is structured as a full-stack monorepo:

```
DemandIQ/
├── backend/                  # Python 3.11 + FastAPI + SQLAlchemy + Alembic
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── api/              # Route handlers (forecast, inventory, alerts, reports, auth, users, health)
│   │   ├── core/             # Configuration, DB session, and security
│   │   ├── ml/               # Forecasting ML pipelines (features, training, inference)
│   │   ├── models/           # SQLAlchemy ORM entities
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   ├── services/         # Business logic layer
│   │   └── main.py           # FastAPI application entrypoint
│   ├── tests/                # Pytest test suite
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Container definition
│
├── frontend/                 # Next.js 14 (App Router) + TypeScript + Tailwind CSS + Recharts
│   ├── app/                  # App router pages (dashboard, forecasts, inventory, alerts, reports, settings, login)
│   ├── components/           # Shared UI components (Sidebar, Navbar, KPICard, ChartWrapper, DataTable, AlertCard, HealthStatus)
│   ├── lib/                  # API client & utility helpers
│   ├── types/                # TypeScript interface definitions
│   ├── package.json          # Node dependencies
│   └── Dockerfile            # Frontend container definition
│
├── docker-compose.yml        # Orchestration for Backend, Frontend, and PostgreSQL
└── README.md
```

---

## 🚀 Quick Start with Docker Compose

The fastest way to spin up the entire platform (PostgreSQL, FastAPI backend, and Next.js frontend):

```bash
# 1. Clone or navigate to the repository
cd DemandIQ

# 2. Copy environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Start all services
docker-compose up --build
```

- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **PostgreSQL**: `localhost:5432` (`demandiq_db`)

---

## 🛠️ Local Development (Without Docker)

### 1. Backend (FastAPI)

Prerequisites: **Python 3.11+**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run test suite:
```bash
pytest
```

### 2. Frontend (Next.js 14)

Prerequisites: **Node.js 18+**, **npm**

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start Next.js dev server
npm run dev
```

The frontend will run on [http://localhost:3000](http://localhost:3000).

---

## 📡 API Health Check & Diagnostics

Check system health directly via cURL or browser:

```bash
curl http://localhost:8000/health
```

Expected Response:
```json
{
  "status": "healthy",
  "service": "DemandIQ Backend",
  "version": "1.0.0",
  "environment": "development",
  "database": "connected",
  "timestamp": "2026-08-25T10:30:00.000000Z"
}
```

---

## 🔒 Security & Best Practices

- Standardized JWT authentication scaffolding (`app/core/security.py`).
- Strict CORS handling configured through environment variables.
- Modular service architecture separating business logic from route controllers.
- Type-safe schemas shared conceptually across Pydantic and TypeScript interfaces.

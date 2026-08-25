# DemandIQ — Intelligent Retail Demand Forecasting & Inventory Optimization

<div align="center">

[![Next.js 14](https://img.shields.io/badge/Next.js-14.2.5-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?style=for-the-badge&logo=vercel)](https://demand-iq-retail-demand-forecasting.vercel.app/login)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://demandiq-backend-m15l.onrender.com/docs)
[![Test Coverage](https://img.shields.io/badge/Coverage-86%25-brightgreen?style=for-the-badge&logo=pytest)](https://pytest.org)

<br/>

### 🌐 **[Launch Live Web Application](https://demand-iq-retail-demand-forecasting.vercel.app/login)** • **[Interactive API Documentation (Swagger)](https://demandiq-backend-m15l.onrender.com/docs)**

</div>

---

## 🌟 Live Cloud Deployment

| Service | Live URL | Hosting Provider | Status |
| :--- | :--- | :--- | :--- |
| **Frontend Web Application** | **[demand-iq-retail-demand-forecasting.vercel.app](https://demand-iq-retail-demand-forecasting.vercel.app/login)** | **Vercel** | 🟢 Live |
| **Backend REST API** | **[demandiq-backend-m15l.onrender.com](https://demandiq-backend-m15l.onrender.com)** | **Render** | 🟢 Live |
| **Interactive Swagger Docs** | **[demandiq-backend-m15l.onrender.com/docs](https://demandiq-backend-m15l.onrender.com/docs)** | **Render** | 🟢 Live |
| **PostgreSQL Database** | **Supabase Managed Postgres** | **Supabase** | 🟢 Live |

---

### 🔑 1-Click Quick Demo Login Credentials

You can use the **1-Click Preset Buttons** directly on the [Login Page](https://demand-iq-retail-demand-forecasting.vercel.app/login) or enter credentials:

| Role | Email | Password | Permissions & Scope |
| :--- | :--- | :--- | :--- |
| 🛡️ **System Administrator** | `admin@demandiq.io` | `adminpassword123` | Full cross-store visibility, user management, and model retraining |
| 📊 **Supply Planner** | `planner@demandiq.io` | `plannerpassword123` | Aggregate visibility across all stores, simulations, and purchase orders |
| 🏬 **Store 1 Manager** | `manager_store1@demandiq.io` | `managerpassword123` | Multi-tenant isolated to **Store 1 (Seattle Flagship)** |

---

## 🚀 Key Platform Capabilities

- 📈 **Ensemble Machine Learning Forecasting**: Blends **Facebook Prophet** (seasonality/trends) and **XGBoost Regression** (lag features, rolling averages, promotional indicators) with 95% shaded confidence bands.
- 📦 **Statistical Inventory Optimization**: Dynamic Safety Stock calculation ($Z \times \sigma_d \times \sqrt{L}$), Reorder Points (ROP), Recommended Order Quantities (ROQ), and Days-of-Cover risk classification (`CRITICAL`, `WARNING`, `OK`).
- ⚡ **Real-Time Anomaly & Stockout Alerting**: Automated rolling Z-score shock detection ($Z \ge 4.0\sigma$) and multivariate Isolation Forest category screening.
- 🎯 **What-If Promotional Simulator**: Interactive markdown/uplift sensitivity analysis with live Recharts response curves.
- 🏢 **Multi-Tenant Role-Based Access Control (RBAC)**: Enforced store-level multi-tenancy and data isolation.
- 📊 **Observability & Health Probes**: Structured JSON access logs with request-latency metrics, `/health` (Liveness), and `/ready` (Readiness) probes.

---

## 🏗️ Monorepo Architecture

```text
DemandIQ/
├── backend/                  # Python 3.11 + FastAPI + SQLAlchemy + Alembic
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── api/v1/           # Modular REST API route handlers
│   │   ├── core/             # Config, security, DB session, structured JSON logging
│   │   ├── ml/               # Prophet, XGBoost, and Ensemble models + inference
│   │   ├── models/           # SQLAlchemy ORM entities (PostgreSQL)
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   ├── services/         # Business logic layer
│   │   └── main.py           # FastAPI application entrypoint
│   ├── tests/                # 42 Pytest tests (86% coverage)
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Multi-stage Python 3.11 container (Gunicorn + Uvicorn)
│
├── frontend/                 # Next.js 14 (App Router) + TypeScript + Tailwind CSS + Recharts
│   ├── app/                  # App router pages (/dashboard, /forecasts, /inventory, /alerts, /reports, /settings, /login)
│   ├── components/           # Shared UI components (Sidebar, Navbar, KPICard, ChartWrapper, DataTable, AlertCard)
│   ├── lib/                  # Typed API client with JWT refresh handling & utils
│   ├── types/                # TypeScript interface definitions
│   ├── package.json          # Node dependencies
│   └── Dockerfile            # Standalone Next.js runner
│
├── .github/workflows/        # CI/CD GitHub Actions pipelines
├── docker-compose.yml        # Multi-profile orchestration (dev vs prod)
├── DEPLOYMENT.md             # Operations & migration manual
└── README.md
```

---

## 💻 Local Development Setup

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Docker & Docker Compose** (Optional)

### 2. Running Locally (FastAPI + Next.js)

```bash
# Terminal 1 — Backend:
cd backend
python -m venv venv
.\venv\Scripts\activate            # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Frontend:
cd frontend
npm install
npm run dev
```

- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Probe**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Testing & Code Quality

### Backend Test Suite (Pytest + Coverage)
```bash
cd backend
pytest --cov=app --cov-report=term-missing
```
*Result: **42/42 tests passing** with **86% code coverage**.*

### Frontend Production Build Verification
```bash
cd frontend
npm run build
```

---

## 📄 License

This project is licensed under the MIT License.

<p align="center">
  <img src="https://img.shields.io/badge/FraudLens-1.0-blueviolet?style=for-the-badge&logoColor=white" alt="FraudLens 1.0"/>
  <img src="https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge" alt="Status"/>
  <img src="https://img.shields.io/github/actions/workflow/status/ajinkyachalke008/FraudLens/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"/>
  <img src="https://img.shields.io/github/license/ajinkyachalke008/FraudLens?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">🔍 FraudLens</h1>
<h3 align="center">Real-Time Graph Intelligence Platform for Financial Fraud Detection</h3>

<p align="center">
  An enterprise-grade cybercrime intelligence platform that leverages <b>Graph Neural Networks</b>, <b>real-time streaming</b>, and <b>interactive graph visualization</b> to detect, analyze, and intercept complex financial fraud syndicates.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Next.js_15-black?style=flat-square&logo=next.js&logoColor=white" alt="Next.js"/>
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Neo4j-018bff?style=flat-square&logo=neo4j&logoColor=white" alt="Neo4j"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Redis-DD0031?style=flat-square&logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/Kafka-231F20?style=flat-square&logo=apachekafka&logoColor=white" alt="Kafka"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" alt="PyTorch"/>
  <img src="https://img.shields.io/badge/D3.js-F9A03C?style=flat-square&logo=d3.js&logoColor=black" alt="D3.js"/>
</p>

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [ML Pipeline](#-ml-pipeline)
- [Environment Variables](#-environment-variables)
- [Available Commands](#-available-commands)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔄 **Real-Time Kafka Streaming** | High-throughput transaction ingestion via Apache Kafka with 6 partitioned topics |
| 🧠 **FraudSAGE (GNN)** | 2-layer GraphSAGE neural network for inductive fraud risk scoring on transaction graphs |
| 🌲 **Isolation Forest** | Unsupervised anomaly detection for high-velocity transaction burst patterns |
| 📊 **DBSCAN Clustering** | Density-based clustering on GNN embeddings to identify fraud syndicates |
| 🎯 **SHAP Explainability** | Model-agnostic explanations for every fraud prediction, enabling audit trails |
| 📡 **Live Mission Control** | Real-time WebSocket streaming via Redis Pub/Sub to a dark-mode Next.js dashboard |
| 🕸️ **Interactive Graph Intel** | D3.js force-directed graph visualization with 2nd/3rd-degree network exploration |
| 📁 **Automated Case Management** | Auto-generated case files with escalation based on ML risk scores and centrality |
| 🔐 **JWT Authentication** | Secure role-based access with bcrypt password hashing and token refresh |
| 📈 **Excel/CSV Ingestion** | Bulk transaction ingestion from Excel files with fuzzy entity resolution |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Next.js 15 + React 19 + TailwindCSS + D3.js + Recharts     │  │
│  │  Port: 3000                                                  │  │
│  └──────────────────────┬───────────────────────────────────────┘  │
│                         │ HTTP / WebSocket                         │
├─────────────────────────┼──────────────────────────────────────────┤
│                    API GATEWAY                                     │
│  ┌──────────────────────┴───────────────────────────────────────┐  │
│  │  FastAPI (Async Python)                                      │  │
│  │  Port: 8000                                                  │  │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐          │  │
│  │  │  Auth   │ │  Ingest  │ │  Graph │ │    ML    │          │  │
│  │  │  API    │ │  API     │ │  API   │ │  API     │          │  │
│  │  └─────────┘ └──────────┘ └────────┘ └──────────┘          │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐      │  │
│  │  │  Dashboard   │ │    Cases     │ │   WebSockets   │      │  │
│  │  │  API         │ │    API       │ │   (Pub/Sub)    │      │  │
│  │  └──────────────┘ └──────────────┘ └────────────────┘      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                         │                                          │
├─────────────────────────┼──────────────────────────────────────────┤
│                    ML ENGINE                                       │
│  ┌──────────────┐ ┌────────────────┐ ┌─────────────────────────┐  │
│  │  FraudSAGE   │ │ Isolation      │ │  SHAP Explainer         │  │
│  │  (GraphSAGE) │ │ Forest         │ │  (Model Interpretability│  │
│  │  PyTorch     │ │ scikit-learn   │ │   & Audit Trails)       │  │
│  │  Geometric   │ │                │ │                         │  │
│  └──────────────┘ └────────────────┘ └─────────────────────────┘  │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                   DATA & STREAMING LAYER                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ PostgreSQL│  │  Neo4j   │  │  Redis   │  │  Apache Kafka     │ │
│  │  (Users,  │  │ (Graph   │  │ (Cache,  │  │  (Event Streaming │ │
│  │  Cases,   │  │  Accounts│  │  PubSub, │  │   raw-transactions│ │
│  │  Audit)   │  │  & Txns) │  │  Rate    │  │   ml-scores,      │ │
│  │  :5432    │  │  :7687   │  │  Limit)  │  │   fraud-alerts)   │ │
│  │           │  │  :7474   │  │  :6379   │  │   :9092           │ │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Async Python web framework for high-performance APIs |
| **SQLAlchemy 2.0** | Async ORM with PostgreSQL (asyncpg driver) |
| **Alembic** | Database migration management |
| **Neo4j Python Driver** | Graph database interaction |
| **aiokafka** | Async Kafka producer/consumer |
| **PyTorch + PyG** | Graph Neural Network (FraudSAGE) |
| **scikit-learn** | Isolation Forest & DBSCAN clustering |
| **SHAP** | ML model explainability |
| **python-jose + bcrypt** | JWT auth & password hashing |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Next.js 15** | React framework with App Router |
| **React 19** | UI component library |
| **TailwindCSS** | Utility-first CSS framework |
| **D3.js** | Interactive force-directed graph visualization |
| **Recharts** | Dashboard charts and analytics |
| **Framer Motion** | Smooth UI animations |
| **Zustand** | Lightweight state management |
| **React Query** | Server state management & caching |
| **Zod** | Runtime schema validation |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| **PostgreSQL 16** | Relational data (users, cases, audit logs) |
| **Neo4j 5.15** | Graph storage (accounts & transactions) |
| **Redis 7** | Caching, rate limiting, WebSocket Pub/Sub |
| **Apache Kafka** | Distributed event streaming |
| **Docker Compose** | Multi-service orchestration |

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** installed
- **Ports available**: `3000`, `8000`, `5432`, `7474`, `7687`, `6379`, `9092`

### One-Click Deployment

#### Linux / macOS
```bash
git clone https://github.com/ajinkyachalke008/FraudLens.git
cd FraudLens
bash start.sh
```

#### Windows (PowerShell)
```powershell
git clone https://github.com/ajinkyachalke008/FraudLens.git
cd FraudLens
.\deploy.ps1
```

**The deployment script will automatically:**
1. 🐳 Build production Docker containers
2. 🔧 Boot infrastructure services (Postgres, Neo4j, Redis)
3. 📊 Run Alembic database migrations
4. 🌱 Seed the database with demo data & admin accounts
5. 🚀 Launch the FastAPI backend & Next.js frontend

### Access the Platform

| Service | URL |
|---------|-----|
| 🖥️ **Mission Control Dashboard** | [http://localhost:3000](http://localhost:3000) |
| 📚 **API Documentation (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| 🔗 **Neo4j Browser** | [http://localhost:7474](http://localhost:7474) |

**Default Admin Credentials:**
```
Email:    investigator@fraudlens.gov
Password: fraudlens2026
```

---

## 📂 Project Structure

```
FraudLens/
├── backend/                    # FastAPI Backend
│   ├── api/
│   │   ├── deps.py             # Dependency injection (DB sessions, auth)
│   │   └── v1/
│   │       ├── router.py       # Central API router
│   │       └── endpoints/
│   │           ├── auth.py         # JWT login/register
│   │           ├── ingest.py       # Excel/CSV bulk ingestion
│   │           ├── graph.py        # Neo4j graph queries
│   │           ├── predict.py      # Real-time ML predictions
│   │           ├── ml.py           # ML dashboard & model stats
│   │           ├── dashboard.py    # Mission Control metrics
│   │           ├── cases.py        # Case CRUD & escalation
│   │           └── websockets.py   # Live event streaming
│   ├── core/
│   │   ├── database.py         # Async SQLAlchemy engine
│   │   ├── neo4j.py            # Neo4j driver management
│   │   ├── cache.py            # Redis/In-Memory caching
│   │   ├── pubsub.py           # Redis Pub/Sub for WebSockets
│   │   └── security.py         # JWT token & password utilities
│   ├── ml/
│   │   ├── models/
│   │   │   ├── gnn.py              # FraudSAGE (GraphSAGE) model
│   │   │   ├── isolation_forest.py # Anomaly detection model
│   │   │   └── clustering.py       # DBSCAN syndicate clustering
│   │   └── explainability/
│   │       └── shap_explainer.py   # SHAP-based model explanations
│   ├── models/
│   │   ├── sql/                # SQLAlchemy ORM models
│   │   │   ├── user.py, case.py, transaction.py, account.py
│   │   │   └── base.py
│   │   └── schemas/            # Pydantic request/response schemas
│   │       ├── ingest.py
│   │       └── graph.py
│   ├── services/
│   │   └── ingestion/
│   │       ├── excel_parser.py     # Excel file parsing & validation
│   │       └── graph_writer.py     # Neo4j graph construction
│   ├── streaming/
│   │   ├── producer.py         # Kafka message producer
│   │   └── consumer.py         # Kafka message consumer
│   ├── scripts/
│   │   ├── seed_test_data.py   # Database seeder
│   │   ├── init_db.sql         # PostgreSQL initialization
│   │   └── init_neo4j.cypher   # Neo4j constraints & indexes
│   ├── alembic/                # Database migrations
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile
│
├── frontend/                   # Next.js Frontend
│   ├── app/
│   │   ├── (auth)/login/       # Login page
│   │   ├── (dashboard)/
│   │   │   ├── graph/          # Interactive graph explorer
│   │   │   └── ml/             # ML model dashboard
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Landing / dashboard page
│   │   ├── providers.tsx       # React Query + Auth providers
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── graph/
│   │   │   ├── TransactionGraph.tsx  # D3.js force graph
│   │   │   └── GraphSidebar.tsx      # Graph controls & filters
│   │   ├── layout/
│   │   │   ├── GlobalSidebar.tsx     # Navigation sidebar
│   │   │   └── TopBar.tsx            # Top navigation bar
│   │   └── ui/                       # Reusable UI components
│   ├── contexts/AuthContext.tsx       # Authentication context
│   ├── hooks/
│   │   ├── useDashboardData.ts       # Dashboard data fetching
│   │   └── useTransactionStream.ts   # WebSocket stream hook
│   ├── middleware.ts                  # Auth route protection
│   └── package.json
│
├── docker-compose.yml          # Production services
├── docker-compose.tools.yml    # Dev tools (Kafka UI, etc.)
├── deploy.ps1                  # Windows deployment script
├── deploy_native.ps1           # Native (non-Docker) deployment
├── start.sh                    # Linux/macOS deployment script
├── Makefile                    # Developer command shortcuts
└── README.md
```

---

## 📡 API Reference

Base URL: `http://localhost:8000/api/v1`

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | Authenticate & receive JWT token |
| `POST` | `/auth/register` | Register a new investigator account |

### Data Ingestion
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest/upload` | Upload Excel/CSV transaction files |

### Graph Intelligence
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/graph/accounts` | Fetch all accounts as graph nodes |
| `GET` | `/graph/transactions` | Fetch transaction edges |
| `GET` | `/graph/neighbors/{id}` | Get N-degree neighbors of an account |

### Machine Learning
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict/score` | Run FraudSAGE inference on accounts |
| `GET` | `/ml/stats` | Model performance metrics |
| `POST` | `/ml/cluster` | Run DBSCAN clustering on embeddings |

### Case Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/cases` | List all investigation cases |
| `POST` | `/cases` | Create a new case |
| `PATCH` | `/cases/{id}` | Update case status/priority |

### Mission Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/stats` | Real-time platform statistics |
| `WS` | `/ws/live` | WebSocket for live transaction feed |

> 📖 Full interactive API documentation available at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧠 ML Pipeline

### FraudSAGE — Graph Neural Network

A **2-layer GraphSAGE** model that learns inductive node representations from the transaction graph:

```
Input Features (per account):
├── total_inflow      — Sum of incoming transaction amounts
├── total_outflow     — Sum of outgoing transaction amounts
├── balance_ratio     — inflow / outflow ratio
└── degree_centrality — Number of unique transaction partners

Architecture:
├── SAGEConv Layer 1 (4 → 16) + BatchNorm + ReLU + Dropout(0.3)
├── SAGEConv Layer 2 (16 → 16) + BatchNorm + ReLU + Dropout(0.3)
└── Linear Layer (16 → 1) + Sigmoid → Risk Score [0, 1]
```

### Isolation Forest — Anomaly Detection
Detects statistically anomalous transaction patterns (velocity spikes, unusual amounts, off-hours activity).

### DBSCAN Clustering
Groups accounts by GNN embedding similarity to identify **coordinated fraud rings** operating as syndicates.

### SHAP Explainability
Every prediction comes with feature-level SHAP values, enabling transparent and auditable fraud decisions.

---

## ⚙️ Environment Variables

Create `backend/.env` with the following:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fraudlens

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fraudlens2025

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Auth
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Frontend
FRONTEND_URL=http://localhost:3000
```

---

## 🧰 Available Commands

FraudLens ships with a comprehensive `Makefile` for developer productivity:

```bash
# ── Services ──
make up                  # Start all Docker services
make down                # Stop all services
make restart             # Restart all services
make health              # Health check all services

# ── Development ──
make backend             # Start FastAPI dev server
make frontend            # Start Next.js dev server
make both                # Start both simultaneously
make install             # Install all dependencies

# ── Database ──
make db-migrate          # Run Alembic migrations
make db-rollback         # Rollback last migration
make db-reset            # Reset database completely
make seed                # Load demo/test data

# ── Infrastructure ──
make neo4j-init          # Run Neo4j constraints & indexes
make kafka-create-topics # Create all Kafka topics
make redis-flush         # Flush Redis cache
make redis-monitor       # Monitor Redis commands live

# ── Quality ──
make test                # Run all tests
make lint                # Lint Python + TypeScript
make format              # Auto-format all code
make security            # Run security audit (bandit + safety)

# ── Maintenance ──
make clean               # Remove build artifacts
make logs                # Tail all service logs
make logs-backend        # Tail backend logs only
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>Built for the future of cybercrime intelligence.</b><br/>
  <sub>Made with ❤️ by <a href="https://github.com/ajinkyachalke008">Ajinkya Chalke</a></sub>
</p>

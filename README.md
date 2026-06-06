# FraudLens 1.0 — Cybercrime Intelligence Platform

![FraudLens Architecture](https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Next JS](https://img.shields.io/badge/Next-black?style=for-the-badge&logo=next.js&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-018bff?style=for-the-badge&logo=neo4j&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

**FraudLens** is an enterprise-grade, real-time graph intelligence platform built specifically to detect, analyze, and intercept complex financial fraud syndicates.

## 🌟 Key Features
- **Real-time Kafka Streaming**: High-throughput transaction ingestion using Apache Kafka.
- **Graph Neural Network (FraudSAGE)**: Live ML inference that clusters accounts in real-time based on their transactional embeddings.
- **Isolation Forest**: Unsupervised anomaly detection for high-velocity transaction bursts.
- **Live Mission Control**: Real-time websocket streaming powered by Redis Pub/Sub directly to a sleek, dark-mode Next.js UI.
- **Interactive D3.js Graph Intel**: Visual exploration of 2nd and 3rd-degree network connections for deep syndicate investigations.
- **Automated Case Generation**: Automatically opens and escalates case files based on ML risk scores and centrality measures.

---

## 🏗️ Architecture

FraudLens is composed of 7 independent microservices running via Docker Compose:

1. **Next.js Frontend (`frontend`)**: React 18 / Next.js 15, TailwindCSS, D3.js, Lucide Icons.
2. **FastAPI Backend (`backend`)**: Async Python API handling Auth, ML inference, Graph querying, and WebSockets.
3. **Neo4j (`neo4j`)**: Graph database storing Accounts (Nodes) and Transactions (Relationships).
4. **PostgreSQL (`postgres`)**: Relational database storing Users, Roles, Cases, and Audit Logs.
5. **Redis (`redis`)**: In-memory data store for Caching, Rate Limiting, and WebSocket Pub/Sub brokering.
6. **Kafka (`kafka`)**: High-throughput distributed event streaming platform.
7. **Zookeeper (`zookeeper`)**: Configuration manager for Kafka.

---

## 🚀 Quickstart (Production Deployment)

We've bundled the entire 7-service architecture into a single automated boot script. 

### Prerequisites
- Docker & Docker Compose installed.
- Ports `3000`, `8000`, `5432`, `7687`, `6379`, `9092` must be available on your machine.

### Launch
Simply run the master deployment script from the root directory:
```bash
bash start.sh
```

**The script will automatically:**
1. Build the production Docker containers.
2. Boot up the infrastructure layer.
3. Inject the Neo4j graph constraints and indexes.
4. Run the PostgreSQL Alembic database migrations.
5. Seed the database with ML dummy data and Admin accounts.
6. Launch the FastAPI backend and Next.js frontend.

---

## 🔐 Access Credentials

Once the `start.sh` script completes, the platform will be available at:

- **Mission Control Dashboard**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

**Default Admin Account:**
- **Email:** `investigator@fraudlens.gov`
- **Password:** `fraudlens2026`

---

## 🛠️ Local Development

If you wish to develop locally without the production Docker wrapper:

1. **Boot Infrastructure Only**:
   ```bash
   docker-compose up -d postgres neo4j redis kafka zookeeper
   ```
2. **Run FastAPI Backend**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   python scripts/seed_test_data.py
   uvicorn main:app --reload --port 8000
   ```
3. **Run Next.js Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---
*Built for the future of cybercrime intelligence.*

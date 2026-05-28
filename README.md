# FraudLens

Graph intelligence platform for financial fraud investigation, built from the master platform reference.

## What Is Included

- Next.js 15 frontend with App Router dashboard, graph workspace, ML scoring, central nodes, ingest, cases, reports, and settings screens.
- FastAPI backend with versioned API routes for auth, ingest, graph, ML, nodes, cases, reports, alerts, and digital arrest detection.
- PostgreSQL schema for users, cases, accounts, transactions, ML scores, evidence, reports, digital arrest events, audit logs, and ingestion jobs.
- Neo4j constraints and graph service stubs for account and transaction traversal.
- ML service skeleton for Isolation Forest, Random Forest, K-Means, ensemble scoring, SHAP explanations, and PyTorch Geometric GNN.
- Docker Compose stack for frontend, backend, PostgreSQL, Neo4j, Redis, Kafka, and Zookeeper.
- CI workflow, docs, seed script, and backend unit test for ensemble scoring.

## Quick Start

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

Frontend: http://localhost:3000

API docs: http://localhost:8000/docs

Neo4j Browser: http://localhost:7474

## Local Commands

```bash
make dev
make backend
make frontend
make test-backend
make typecheck-frontend
```

## Default Demo Login

```text
Email: investigator@fraudlens.local
Password: fraudlens
```

The current login screen is UI-only; the FastAPI auth route already returns JWT-shaped access and refresh tokens for development.

## Project Layout

```text
frontend/      Next.js investigation workspace
backend/       FastAPI API, services, workers, schemas, tests
backend/db/    PostgreSQL schema and Neo4j constraints
docs/          Architecture, API, and police data format notes
models/        Ignored ML artifact location
notebooks/     Exploratory analysis workspace
```

## Phase 1 Status

This is a scaffold with working route contracts and demo data. The next concrete engineering step is wiring ingestion writes into PostgreSQL and Neo4j, then replacing frontend demo data with TanStack Query calls to the FastAPI routes.

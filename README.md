# FraudLens: Ultimate Cybercrime Intelligence Platform

FraudLens is an advanced, enterprise-grade Cybercrime Management and Intelligence Platform designed for Law Enforcement and Financial Institutions. It provides end-to-end capabilities spanning live transaction ingestion, Neo4j graph network analysis, geospatial IP tracking, external OSINT enrichment, and cryptographic court-ready PDF generation.

## 🚀 Key Features

### 1. Live Ingestion Engine
- **Asynchronous Processing**: Ingests massive volumes of real-time financial transactions via Kafka/WebSocket pipelines.
- **Rules Engine**: Automatically flags transactions exceeding volume thresholds, anomalous timings, or interacting with high-risk IFSC branches.

### 2. Multi-Case Syndicate Detection
- **Neo4j Network Graphs**: Visualizes complex money laundering rings using D3.js physics simulations.
- **Cross-Case Intelligence**: Scans the PostgreSQL database using powerful aggregations to instantly flag "Shared Suspects" operating across multiple isolated police cases.

### 3. Open Source Intelligence (OSINT)
- **Crypto Forensics**: Simulates blockchain intelligence to attribute wallets to known ransomware clusters.
- **Social Hunting**: Simulates a cross-platform username hunt across Twitter, Telegram, Reddit, and GitHub.
- **IP & Phone Intelligence**: Extracts Shodan-style ASN infrastructure details and Truecaller-style spam reputation scores.

### 4. Court-Ready Documentation (Export Engine)
- Generates official **First Information Reports (FIRs)** in PDF format via `reportlab`.
- Generates official **Charge Sheets** in DOCX format via `python-docx`.
- Employs **Cryptographic Hashing (SHA-256)** seals to ensure the integrity of exported court documents.

---

## 🏗️ Technology Stack

- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS, D3.js, Lucide Icons.
- **Backend**: Python 3.12, FastAPI, SQLAlchemy (Async), Uvicorn.
- **Relational Database**: PostgreSQL 15.
- **Graph Database**: Neo4j 5.20.
- **Orchestration**: Docker & Docker Compose.

---

## 🛠️ Enterprise Deployment (Docker)

FraudLens is designed to be deployed in high-security, air-gapped environments using Docker Compose.

### Prerequisites
- Docker Engine & Docker Compose installed.
- Minimum 4GB RAM available for Neo4j and PostgreSQL.

### Setup Instructions
1. Clone the repository.
2. Rename `.env.example` to `.env` and configure your secure passwords.
3. Build and deploy the cluster:
   ```bash
   docker-compose up --build -d
   ```
4. Access the platforms:
   - **Frontend UI**: `http://localhost:3000`
   - **Backend API Docs**: `http://localhost:8001/docs`
   - **Neo4j Browser**: `http://localhost:7474`

---

## 📝 Project Phases Completed
- [x] Phase 1: Core AI & Graph Database Foundation
- [x] Phase 2: Fraud Detection Pipeline
- [x] Phase 3: Ultimate Case Management Dashboard
- [x] Phase 4: Geospatial & Link Analysis Modules
- [x] Phase 5: Real-Time Live Streaming Simulation
- [x] Phase 6.1: Official Reporting & Export Framework
- [x] Phase 6.2: Cross-Case Syndicate Intelligence
- [x] Phase 6.3: External OSINT Intelligence Platform
- [x] Phase 6.4: Enterprise Deployment & DevOps
- [x] Phase 7: Final Polish & Documentation

---
*Built as a cutting-edge technical demonstration for Advanced Agentic Coding.*

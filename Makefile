.PHONY: up down restart logs backend frontend install test lint format clean neo4j-init db-migrate celery flower

up:
	docker-compose -f docker-compose.yml -f docker-compose.tools.yml up -d

down:
	docker-compose -f docker-compose.yml -f docker-compose.tools.yml down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-neo4j:
	docker-compose logs -f neo4j

logs-kafka:
	docker-compose logs -f kafka

backend:
	cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

both:
	concurrently "make backend" "make frontend"

install-backend:
	cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

install:
	make install-backend && make install-frontend

neo4j-init:
	docker exec -i $$(docker ps -qf "name=neo4j") cypher-shell -u neo4j -p fraudlens2025 < backend/scripts/init_neo4j.cypher

db-migrate:
	cd backend && source .venv/bin/activate && alembic upgrade head

db-rollback:
	cd backend && source .venv/bin/activate && alembic downgrade -1

db-revision:
	cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "$(name)"

db-reset:
	docker-compose down -v && docker-compose up -d postgres && sleep 5 && make db-migrate


test-backend:
	cd backend && source .venv/bin/activate && pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

test-frontend:
	cd frontend && npm run test

test:
	make test-backend && make test-frontend

lint-backend:
	cd backend && source .venv/bin/activate && ruff check . && mypy .

lint-frontend:
	cd frontend && npm run lint

lint:
	make lint-backend && make lint-frontend

format-backend:
	cd backend && source .venv/bin/activate && ruff format .

format-frontend:
	cd frontend && npx prettier --write .

format:
	make format-backend && make format-frontend

security:
	cd backend && source .venv/bin/activate && bandit -r . -x .venv,tests && safety check

kafka-topics:
	docker exec -it $$(docker ps -qf "name=kafka") kafka-topics --list --bootstrap-server localhost:9092

kafka-create-topics:
	docker exec -it $$(docker ps -qf "name=kafka") kafka-topics --create --bootstrap-server localhost:9092 --topic raw-transactions --partitions 6 --replication-factor 1 || true
	docker exec -it $$(docker ps -qf "name=kafka") kafka-topics --create --bootstrap-server localhost:9092 --topic ml-scores --partitions 3 --replication-factor 1 || true
	docker exec -it $$(docker ps -qf "name=kafka") kafka-topics --create --bootstrap-server localhost:9092 --topic fraud-alerts --partitions 3 --replication-factor 1 || true
	docker exec -it $$(docker ps -qf "name=kafka") kafka-topics --create --bootstrap-server localhost:9092 --topic account-updates --partitions 3 --replication-factor 1 || true
	docker exec -it $$(docker ps -qf "name=kafka") kafka-topics --create --bootstrap-server localhost:9092 --topic system-events --partitions 1 --replication-factor 1 || true

redis-flush:
	docker exec -it $$(docker ps -qf "name=redis") redis-cli FLUSHDB

redis-monitor:
	docker exec -it $$(docker ps -qf "name=redis") redis-cli MONITOR

neo4j-clear:
	docker exec -it $$(docker ps -qf "name=neo4j") cypher-shell -u neo4j -p fraudlens2025 "MATCH (n) DETACH DELETE n"

seed:
	cd backend && source .venv/bin/activate && python scripts/seed_test_data.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next frontend/out 2>/dev/null || true
	docker system prune -f

health:
	@echo "Checking all services..."
	@curl -s http://localhost:8000/health && echo " FastAPI OK" || echo " FastAPI FAIL"
	@curl -s http://localhost:3000 > /dev/null && echo " Next.js OK" || echo " Next.js FAIL"
	@curl -s http://localhost:7474 > /dev/null && echo " Neo4j OK" || echo " Neo4j FAIL"
	@docker exec $$(docker ps -qf "name=redis") redis-cli ping | grep -q PONG && echo " Redis OK" || echo " Redis FAIL"
	@docker exec $$(docker ps -qf "name=postgres") pg_isready -U postgres | grep -q accepting && echo " PostgreSQL OK" || echo " PostgreSQL FAIL"

help:
	@echo "FraudLens dev commands:"
	@echo "  make up            Start all Docker services"
	@echo "  make down          Stop all services"
	@echo "  make backend       Start FastAPI dev server"
	@echo "  make frontend      Start Next.js dev server"
	@echo "  make both          Start backend + frontend together"
	@echo "  make install       Install all Python + Node deps"
	@echo "  make neo4j-init    Run Neo4j constraints + indexes"
	@echo "  make db-migrate    Run Alembic migrations"
	@echo "  make kafka-create-topics  Create all 5 Kafka topics"
	@echo "  make test          Run all tests"
	@echo "  make lint          Lint Python + TypeScript"
	@echo "  make format        Auto-format all code"
	@echo "  make health        Check all service health"
	@echo "  make seed          Load test data"
	@echo "  make clean         Remove build artifacts"

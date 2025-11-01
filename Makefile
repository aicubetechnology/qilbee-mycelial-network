.PHONY: help setup up down logs test clean build restart

# Default target
help:
	@echo "Qilbee Mycelial Network - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make setup        - Initial setup (install dependencies)"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs from all services"
	@echo "  make logs-{svc}   - View logs from specific service"
	@echo "  make test         - Run test suite"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make build        - Build Docker images"
	@echo "  make restart      - Restart all services"
	@echo "  make shell-{svc}  - Open shell in service container"
	@echo ""
	@echo "Services: identity, keys, router, hyphal_memory, postgres, mongo, redis"

# Setup
setup:
	@echo "Setting up Qilbee Mycelial Network..."
	pip install -e ./sdk[dev]
	@echo "Setup complete!"

# Docker Compose operations
up:
	@echo "Starting QMN services..."
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  - Identity Service:     http://localhost:8100"
	@echo "  - Keys Service:         http://localhost:8101"
	@echo "  - Router Service:       http://localhost:8200"
	@echo "  - Hyphal Memory:        http://localhost:8201"
	@echo "  - Prometheus:           http://localhost:9090"
	@echo "  - Grafana:              http://localhost:3000 (admin/admin)"
	@echo "  - PostgreSQL:           localhost:5432"
	@echo "  - MongoDB:              localhost:27017"

down:
	@echo "Stopping QMN services..."
	docker-compose down

logs:
	docker-compose logs -f

logs-identity:
	docker-compose logs -f identity

logs-keys:
	docker-compose logs -f keys

logs-router:
	docker-compose logs -f router

logs-hyphal:
	docker-compose logs -f hyphal_memory

logs-postgres:
	docker-compose logs -f postgres

logs-mongo:
	docker-compose logs -f mongo

# Build
build:
	@echo "Building Docker images..."
	docker-compose build

rebuild:
	@echo "Rebuilding Docker images..."
	docker-compose build --no-cache

# Restart
restart:
	@echo "Restarting services..."
	docker-compose restart

restart-identity:
	docker-compose restart identity

restart-keys:
	docker-compose restart keys

restart-router:
	docker-compose restart router

restart-hyphal:
	docker-compose restart hyphal_memory

# Shell access
shell-identity:
	docker-compose exec identity /bin/bash

shell-keys:
	docker-compose exec keys /bin/bash

shell-router:
	docker-compose exec router /bin/bash

shell-hyphal:
	docker-compose exec hyphal_memory /bin/bash

shell-postgres:
	docker-compose exec postgres psql -U postgres -d qmn

shell-mongo:
	docker-compose exec mongo mongosh qmn

# Testing
test:
	@echo "Running tests..."
	pytest tests/unit -v --cov=qilbee_mycelial_network --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration -v

test-e2e:
	@echo "Running end-to-end tests..."
	pytest tests/e2e -v

test-all:
	@echo "Running all tests..."
	pytest tests/ -v --cov=qilbee_mycelial_network --cov-report=html

# Code quality
lint:
	@echo "Running linters..."
	ruff check .
	black --check .

format:
	@echo "Formatting code..."
	black .
	ruff check --fix .

typecheck:
	@echo "Running type checks..."
	mypy --strict sdk/qilbee_mycelial_network

# Cleanup
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"

clean-data:
	@echo "WARNING: This will delete all data volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "Data volumes deleted!"; \
	fi

# Database operations
db-migrate:
	@echo "Running database migrations..."
	docker-compose exec postgres psql -U postgres -d qmn -f /docker-entrypoint-initdb.d/init.sql

db-reset:
	@echo "Resetting database..."
	docker-compose down postgres
	docker volume rm qilbee-mycelial-network_postgres_data || true
	docker-compose up -d postgres
	@echo "Database reset complete!"

# Health checks
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8100/health | jq . || echo "Identity: DOWN"
	@curl -s http://localhost:8101/health | jq . || echo "Keys: DOWN"
	@curl -s http://localhost:8200/health | jq . || echo "Router: DOWN"
	@curl -s http://localhost:8201/health | jq . || echo "Hyphal Memory: DOWN"

# Development
dev:
	@echo "Starting development environment..."
	docker-compose up -d postgres mongo redis prometheus grafana
	@echo "Infrastructure ready. Start services manually for development."

# Generate sample data
seed:
	@echo "Seeding sample data..."
	python scripts/seed_data.py

# Documentation
docs:
	@echo "Building documentation..."
	cd docs && make html

docs-serve:
	@echo "Serving documentation..."
	cd docs/_build/html && python -m http.server 8080

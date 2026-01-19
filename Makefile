# Inventory Management System - Development Makefile

.PHONY: help install dev-setup test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install project dependencies"
	@echo "  dev-setup    - Set up development environment"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-property - Run property-based tests only"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code"
	@echo "  type-check   - Run type checking"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start development environment"
	@echo "  docker-down  - Stop development environment"
	@echo "  clean        - Clean up generated files"

# Install dependencies
install:
	poetry install

# Set up development environment
dev-setup: install
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	poetry run pre-commit install
	@echo "Development environment ready!"

# Run all tests
test:
	poetry run pytest --cov=services --cov=shared --cov-report=html --cov-report=term-missing

# Run unit tests only
test-unit:
	poetry run pytest tests/unit/ -v

# Run property-based tests only
test-property:
	poetry run pytest tests/property/ -v

# Run integration tests only
test-integration:
	poetry run pytest tests/integration/ -v

# Lint code
lint:
	poetry run flake8 services/ shared/ tests/
	poetry run mypy services/ shared/

# Format code
format:
	poetry run black services/ shared/ tests/
	poetry run isort services/ shared/ tests/

# Type checking
type-check:
	poetry run mypy services/ shared/

# Build Docker images
docker-build:
	docker-compose build

# Start development environment
docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services should be available at:"
	@echo "  API Gateway: http://localhost:8000"
	@echo "  Inventory Service: http://localhost:8001"
	@echo "  Location Service: http://localhost:8002"
	@echo "  User Service: http://localhost:8003"
	@echo "  Reporting Service: http://localhost:8004"
	@echo "  UI Service: http://localhost:8005"

# Stop development environment
docker-down:
	docker-compose down

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Database operations
db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

db-revision:
	poetry run alembic revision --autogenerate -m "$(MESSAGE)"

# Development server commands
dev-api-gateway:
	poetry run uvicorn services.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload

dev-inventory:
	poetry run uvicorn services.inventory.main:app --host 0.0.0.0 --port 8001 --reload

dev-location:
	poetry run uvicorn services.location.main:app --host 0.0.0.0 --port 8002 --reload

dev-user:
	poetry run uvicorn services.user.main:app --host 0.0.0.0 --port 8003 --reload

dev-reporting:
	poetry run uvicorn services.reporting.main:app --host 0.0.0.0 --port 8004 --reload

dev-ui:
	poetry run uvicorn services.ui.main:app --host 0.0.0.0 --port 8005 --reload
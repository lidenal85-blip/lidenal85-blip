.PHONY: help install dev test docker-up docker-down deploy clean

help:  ## Show help
@echo "Survey Finder Makefile"
@echo ""
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
uv pip install -e ".[dev]"

dev:  ## Run development server
uvicorn survey_finder.bootstrap.app:app --reload --host 0.0.0.0 --port 8000

test:  ## Run tests
pytest -v

test-cov:  ## Run tests with coverage
pytest -v --cov=src/survey_finder --cov-report=html

lint:  ## Run linters
ruff check src/ tests/

format:  ## Format code
ruff format src/ tests/

docker-up:  ## Start Docker services
cd deployment/compose && docker compose -f docker-compose.yml up -d

docker-down:  ## Stop Docker services
cd deployment/compose && docker compose -f docker-compose.yml down

docker-up-dev:  ## Start Docker services (dev)
cd deployment/compose && docker compose -f docker-compose.dev.yml up -d

docker-down-dev:  ## Stop Docker services (dev)
cd deployment/compose && docker compose -f docker-compose.dev.yml down

deploy:  ## Deploy to production
./deployment/scripts/deploy.sh

backup:  ## Create backup
./deployment/scripts/backup.sh

health:  ## Run health check
./deployment/scripts/healthcheck.sh

logs:  ## Show logs
docker logs -f survey-finder-app-1

clean:  ## Clean cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name ".coverage" -delete 2>/dev/null || true
find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true

.DEFAULT_GOAL := help

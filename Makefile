# TrendOps Docker Compose Commands

.PHONY: help build up down restart logs clean init test

help: ## Show this help message
	@echo "TrendOps Docker Management Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build --no-cache

up: ## Start all services
	docker-compose up -d

up-logs: ## Start all services with logs
	docker-compose up

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs for all services
	docker-compose logs -f

logs-crawler: ## Show crawler logs
	docker-compose logs -f crawler

logs-postgres: ## Show postgres logs
	docker-compose logs -f postgres

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all
	docker system prune -f

init: ## Initialize database only
	docker-compose up postgres -d
	sleep 10
	docker-compose run --rm db-init

test: ## Run crawler once for testing
	docker-compose up postgres -d
	sleep 10
	docker-compose run --rm db-init
	docker-compose run --rm crawler

status: ## Show service status
	docker-compose ps

shell-crawler: ## Access crawler container shell
	docker-compose exec crawler /bin/bash

shell-postgres: ## Access postgres container shell
	docker-compose exec postgres psql -U postgres -d postgres

backup-db: ## Backup database
	docker-compose exec postgres pg_dump -U postgres postgres > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Development commands
dev-build: ## Build for development
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

dev-up: ## Start development environment
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production commands
prod-build: ## Build for production
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## Start production environment
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Security commands
setup-env: ## Setup environment file from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "🔒 Created .env file from template"; \
		echo "⚠️  Please edit .env and change POSTGRES_PASSWORD!"; \
	else \
		echo "📁 .env file already exists"; \
	fi

check-env: ## Check if sensitive data is properly configured
	@echo "🔍 Checking environment configuration..."
	@if grep -q "your_secure_password_here" .env 2>/dev/null; then \
		echo "❌ Default password detected in .env file!"; \
		echo "🔧 Please change POSTGRES_PASSWORD in .env file"; \
		exit 1; \
	else \
		echo "✅ Environment configuration looks good"; \
	fi

security-scan: ## Run security checks
	@echo "🛡️  Running security checks..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found"; exit 1; }
	@echo "✅ Docker is installed"
	@echo "🔒 Checking for secrets in git history..."
	@git log --all --full-history -- .env >/dev/null 2>&1 && echo "⚠️  .env file found in git history!" || echo "✅ No .env in git history"

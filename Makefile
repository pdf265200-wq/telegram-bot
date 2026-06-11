.PHONY: help install test coverage lint format clean run dev docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make coverage     - Run tests with coverage"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean temporary files"
	@echo "  make run          - Run bot locally"
	@echo "  make dev          - Run in development mode"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	python run_tests.py

coverage:
	python run_tests.py --cov

lint:
	flake8 bot/ tests/ --max-line-length=120
	mypy bot/ --ignore-missing-imports
	isort bot/ tests/ --check-only

format:
	black bot/ tests/ --line-length=120
	isort bot/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov
	rm -rf temp/* data/backups/*

run:
	python bot/main.py

dev:
	DEBUG=true LOG_LEVEL=DEBUG python bot/main.py

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

db-backup:
	docker-compose exec bot python scripts/backup_db.py

db-restore:
	docker-compose exec bot python scripts/restore_db.py $(FILE)

init-db:
	python -c "from bot.database.models import init_db; init_db()"

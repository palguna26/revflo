.PHONY: install dev build test lint format docker-up docker-down clean help

help:
	@echo "QuantumReview Makefile"
	@echo "----------------------"
	@echo "make install      - Install dependencies for backend and frontend"
	@echo "make dev          - Run local dev servers (requires two terminals)"
	@echo "make build        - Build backend and frontend"
	@echo "make test         - Run backend tests"
	@echo "make lint         - Run validaton checks"
	@echo "make docker-up    - Start full stack with Docker Compose"
	@echo "make docker-down  - Stop Docker stack"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Please run 'cd backend && uvicorn app.main:app --reload' in one terminal"
	@echo "and 'cd frontend && npm run dev' in another."

build:
	cd frontend && npm run build

test:
	cd backend && pytest

lint:
	cd backend && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	cd frontend && npm run lint

format:
	cd backend && black .
	cd frontend && npm run format

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf frontend/dist
	rm -rf backend/.pytest_cache

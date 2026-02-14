# Makefile for ESG Intelligent Analysis System

.PHONY: help install install-dev test lint format type-check security clean build docs run

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-e2e     - Run end-to-end tests"
	@echo "  make lint         - Run all linters"
	@echo "  make format       - Format code with black and isort"
	@echo "  make type-check   - Run type checking with mypy"
	@echo "  make security     - Run security checks"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build package"
	@echo "  make docs         - Generate documentation"
	@echo "  make run          - Run the application"
	@echo "  make pre-commit   - Install and run pre-commit hooks"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	PYTHONPATH=. pytest src/tests/ -v --tb=short

test-unit:
	pytest src/tests/ -v -m "not integration and not e2e" --tb=short

test-integration:
	pytest src/tests/ -v -m integration --tb=short

test-e2e:
	pytest src/tests/ -v -m e2e --tb=short

test-coverage:
	pytest src/tests/ --cov=src --cov-report=html --cov-report=term-missing

# Linting and Formatting
lint:
	@echo "Running flake8..."
	flake8 src src/tests --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running pylint..."
	pylint src --disable=C0103,C0114,R0903,R0913
	@echo "Running complexity check..."
	xenon --max-absolute=15 --max-modules=15 --max-average=A src/

format:
	@echo "Formatting with black..."
	black src src/tests --line-length=100
	@echo "Sorting imports with isort..."
	isort src src/tests --profile=black --line-length=100

format-check:
	@echo "Checking black formatting..."
	black src src/tests --line-length=100 --check
	@echo "Checking isort..."
	isort src src/tests --profile=black --line-length=100 --check-only

# Type Checking
type-check:
	mypy src --ignore-missing-imports --show-error-codes

# Security
security:
	@echo "Running bandit..."
	bandit -r src -f json -o security-report.json || true
	@echo "Running safety check..."
	safety check || true

# Code Quality (all checks)
quality: format-check lint type-check security
	@echo "All quality checks passed!"

# Pre-commit
pre-commit:
	pre-commit install
	pre-commit run --all-files

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Building
build:
	python -m build

# Documentation
docs:
	cd docs && make html || sphinx-build -b html source _build

docs-serve:
	cd docs/_build && python -m http.server 8000

# Running
run:
	streamlit run main.py

run-simple:
	streamlit run main.py -- --mode simple

run-enhanced:
	streamlit run main.py -- --mode enhanced

# Development utilities
run-tests-watch:
	ptw src/tests/ -- --testmon

benchmark:
	pytest src/tests/ -m performance --benchmark-json=benchmark.json

# Docker commands (if using Docker)
docker-build:
	docker build -t esg-analysis:latest .

docker-run:
	docker run -p 8501:8501 esg-analysis:latest

# Utility targets
requirements:
	pip-compile pyproject.toml -o requirements.txt
	pip-compile pyproject.toml --extra dev -o requirements-dev.txt

sync-requirements:
	pip-sync requirements.txt
	
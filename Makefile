.PHONY: install dev test lint format typecheck build clean docker-build docker-start docker-stop help

PYTHON := python3
PIP := pip

help:
	@echo "RLM Runtime - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install package"
	@echo "  make dev         Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test        Run tests"
	@echo "  make lint        Run linter"
	@echo "  make format      Format code"
	@echo "  make typecheck   Run type checker"
	@echo ""
	@echo "Build:"
	@echo "  make build       Build package"
	@echo "  make clean       Clean build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-start  Start Docker REPL"
	@echo "  make docker-stop   Stop Docker REPL"

install:
	$(PIP) install -e .

dev:
	$(PIP) install -e ".[all]"
	$(PIP) install pre-commit
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

test:
	pytest tests/ -v --cov=rlm --cov-report=term-missing

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

format-check:
	ruff format --check src/ tests/

typecheck:
	mypy src/

build:
	$(PYTHON) -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

docker-build:
	docker build -t rlm-runtime:latest -f docker/Dockerfile .

docker-start:
	./scripts/docker-start.sh

docker-stop:
	./scripts/docker-stop.sh

# Quick check before commit (mirrors CI)
check: lint format-check typecheck test
	@echo "✓ All checks passed!"

# Publish to PyPI (requires credentials)
publish: clean build
	twine upload dist/*

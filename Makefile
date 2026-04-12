.PHONY: help install dev-install test test-fast test-all lint type-check format format-check docker-up docker-down docker-build run run-local clean

PYTHON := python3
PIP := pip
DOCKER_COMPOSE := docker-compose

help:
	@echo "Dostępne komendy:"
	@echo "  install       - Instalacja zależności produkcyjnych"
	@echo "  dev-install   - Instalacja zależności deweloperskich"
	@echo "  test          - Uruchomienie testów pytest (bez slow)"
	@echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)"
	@echo "  test-all      - Wszystkie testy włącznie z slow"
	@echo "  lint          - Sprawdzenie lintingu ruff"
	@echo "  type-check    - Sprawdzenie typów mypy"
	@echo "  format        - Formatowanie kodu ruff"
	@echo "  format-check  - Sprawdzenie formatowania kodu"
	@echo "  docker-up     - Uruchomienie usług Docker"
	@echo "  docker-down   - Zatrzymanie usług Docker"
	@echo "  docker-build  - Budowanie obrazów Docker"
	@echo "  run           - Uruchomienie aplikacji w Docker"
	@echo "  run-local     - Uruchomienie aplikacji lokalnie"
	@echo "  clean         - Czyszczenie plików tymczasowych"

install:
	$(PIP) install -r requirements.txt

dev-install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ -v -m "not slow"

test-fast:
	$(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e"

test-all:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check redsl/ tests/

type-check:
	$(PYTHON) -m mypy redsl/

format:
	$(PYTHON) -m ruff format redsl/ tests/
	$(PYTHON) -m ruff check --fix redsl/ tests/

format-check:
	$(PYTHON) -m ruff format --check redsl/ tests/

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-build:
	$(DOCKER_COMPOSE) build

run: docker-up

run-local:
	$(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf refactor_output/ 2>/dev/null || true

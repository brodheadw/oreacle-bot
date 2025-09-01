.PHONY: help dev test run-monitor run-single lint format clean install

# Default target
help:
	@echo "Available targets:"
	@echo "  dev         - Install development dependencies"
	@echo "  install     - Install package in development mode"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting (flake8, mypy)"
	@echo "  format      - Format code (black, isort)"
	@echo "  run-monitor - Run continuous monitoring"
	@echo "  run-single  - Run single cycle"
	@echo "  clean       - Clean build artifacts"

# Development setup
dev:
	pip install -e .[dev]
	@echo "✅ Development environment ready"

install:
	pip install -e .
	@echo "✅ Package installed in development mode"

# Testing
test:
	pytest tests/ -v --tb=short
	@echo "✅ Tests completed"

test-cov:
	pytest tests/ --cov=oreaclebot --cov-report=term-missing --cov-report=html
	@echo "✅ Tests with coverage completed"

# Code quality
lint:
	flake8 oreaclebot/ tests/
	mypy oreaclebot/
	@echo "✅ Linting completed"

format:
	black oreaclebot/ tests/
	isort oreaclebot/ tests/
	@echo "✅ Code formatted"

# Run bot
run-monitor: 
	@echo "🤖 Starting continuous monitoring..."
	@if [ -f .env ]; then source .env; fi; oreaclebot-monitor

run-single:
	@echo "🤖 Running single cycle..."
	@if [ -f .env ]; then source .env; fi; oreaclebot-single

# Check environment
check-env:
	@echo "Checking environment variables..."
	@python -c "import os; print('✅ MANIFOLD_API_KEY:', 'SET' if os.getenv('MANIFOLD_API_KEY') else '❌ MISSING'); print('✅ MARKET_SLUG:', 'SET' if os.getenv('MARKET_SLUG') else '❌ MISSING'); print('✅ OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else '⚠️  OPTIONAL (will use legacy translation if missing)')"

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Cleaned build artifacts"

# CI/CD helpers
ci-test:
	pytest tests/ -v --tb=short --cov=oreaclebot --cov-fail-under=80

ci-lint:
	black --check oreaclebot/ tests/
	isort --check-only oreaclebot/ tests/
	flake8 oreaclebot/ tests/
	mypy oreaclebot/
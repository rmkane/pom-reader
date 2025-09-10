# POM Reader - Makefile
# Modern Python project with comprehensive development targets

.PHONY: help install install-dev build run test test-cov lint format type-check clean clean-all dist publish docs example

# Default target
help: ## Show this help message
	@echo "POM Reader - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Virtual environment management
venv: ## Create virtual environment
	python3 -m venv .venv
	@echo "Virtual environment created in .venv/"
	@echo "Activate it with: source .venv/bin/activate"

venv-activate: ## Show how to activate virtual environment
	@echo "To activate the virtual environment, run:"
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "To deactivate, run:"
	@echo "  deactivate"

venv-status: ## Check virtual environment status
	@if [ "$(HAS_VENV)" = "yes" ]; then \
		echo "✅ Virtual environment exists at .venv/"; \
		if [ -n "$$VIRTUAL_ENV" ]; then \
			echo "✅ Virtual environment is currently active: $$VIRTUAL_ENV"; \
		else \
			echo "⚠️  Virtual environment exists but is not active"; \
			echo "   Activate with: source .venv/bin/activate"; \
		fi; \
	else \
		echo "❌ No virtual environment found"; \
		echo "   Create one with: make venv"; \
	fi

# Installation targets
install: ## Install the package in production mode
	pip install .

install-dev: ## Install the package in development mode with all dev dependencies
	pip install -e ".[dev]"

install-venv: venv ## Create venv and install dev dependencies
	@echo "Installing development dependencies in virtual environment..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	@echo "Virtual environment setup complete!"
	@echo "Activate with: source .venv/bin/activate"

# Build targets
build: clean ## Build the package
	python3 -m build

dist: build ## Create distribution packages
	@echo "Distribution packages created in dist/"

# Development targets
run: ## Run the example script
	$(PYTHON) example.py

example: run ## Alias for run target

# Testing targets
test: ## Run tests with pytest
	$(PYTHON) -m pytest

test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest --cov=pom_reader --cov-report=html --cov-report=term-missing

test-verbose: ## Run tests with verbose output
	$(PYTHON) -m pytest -v

test-watch: ## Run tests in watch mode (requires pytest-watch)
	$(PYTHON) -m ptw

# Code quality targets
lint: ## Run all linting tools
	@echo "Running ruff..."
	$(PYTHON) -m ruff check src/ tests/
	@echo "Running mypy..."
	$(PYTHON) -m mypy src/

format: ## Format code with black and isort
	@echo "Running black..."
	$(PYTHON) -m black src/ tests/ example.py
	@echo "Running isort..."
	$(PYTHON) -m isort src/ tests/ example.py

format-check: ## Check if code is properly formatted
	@echo "Checking black formatting..."
	$(PYTHON) -m black --check src/ tests/ example.py
	@echo "Checking isort formatting..."
	$(PYTHON) -m isort --check-only src/ tests/ example.py

type-check: ## Run type checking with mypy
	$(PYTHON) -m mypy src/

# CLI testing targets
cli-test: ## Test CLI commands
	@echo "Testing CLI analyze command..."
	pom-reader analyze resources/pom.xml --format table
	@echo ""
	@echo "Testing CLI dependencies command..."
	pom-reader dependencies resources/pom.xml
	@echo ""
	@echo "Testing CLI plugins command..."
	pom-reader plugins resources/pom.xml
	@echo ""
	@echo "Testing CLI export command..."
	pom-reader export resources/pom.xml --format json | head -20

# Documentation targets
docs: ## Generate documentation (if using sphinx)
	@echo "Documentation generation not yet implemented"

# Cleaning targets
clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete

clean-all: clean ## Clean everything including virtual environments
	rm -rf .venv/
	rm -rf venv/
	rm -rf env/

# Development workflow targets
dev-setup: install-venv ## Set up development environment with virtual environment
	@echo "Development environment set up!"
	@echo "Activate the virtual environment: source .venv/bin/activate"
	@echo "Then run 'make test' to verify installation"

dev-setup-system: install-dev ## Set up development environment in system Python
	@echo "Development environment set up in system Python!"
	@echo "Run 'make test' to verify installation"

check: format-check lint type-check test ## Run all checks (format, lint, type, test)

ci: check ## Run CI pipeline locally
	@echo "CI pipeline completed successfully!"

# Release targets
version: ## Show current version
	@$(PYTHON) -c "import pom_reader; print(pom_reader.__version__)"

which-python: ## Show which Python is being used
	@echo "Using Python: $(PYTHON)"
	@echo "Using pip: $(PIP)"
	@echo "Virtual environment active: $(IS_VENV_ACTIVE)"
	@echo "Virtual environment exists: $(HAS_VENV)"

bump-patch: ## Bump patch version
	@echo "Bumping patch version..."
	@python3 -c "import re; content=open('pyproject.toml').read(); new_content=re.sub(r'version = \"(\d+)\.(\d+)\.(\d+)\"', lambda m: f'version = \"{m.group(1)}.{m.group(2)}.{int(m.group(3))+1}\"', content); open('pyproject.toml', 'w').write(new_content)"
	@echo "Version bumped!"

bump-minor: ## Bump minor version
	@echo "Bumping minor version..."
	@python3 -c "import re; content=open('pyproject.toml').read(); new_content=re.sub(r'version = \"(\d+)\.(\d+)\.(\d+)\"', lambda m: f'version = \"{m.group(1)}.{int(m.group(2))+1}.0\"', content); open('pyproject.toml', 'w').write(new_content)"
	@echo "Version bumped!"

bump-major: ## Bump major version
	@echo "Bumping major version..."
	@python3 -c "import re; content=open('pyproject.toml').read(); new_content=re.sub(r'version = \"(\d+)\.(\d+)\.(\d+)\"', lambda m: f'version = \"{int(m.group(1))+1}.0.0\"', content); open('pyproject.toml', 'w').write(new_content)"
	@echo "Version bumped!"

# Publishing targets (for when ready to publish)
publish-test: dist ## Publish to test PyPI
	twine upload --repository testpypi dist/*

publish: dist ## Publish to PyPI
	twine upload dist/*

# Docker targets (if needed in the future)
docker-build: ## Build Docker image
	@echo "Docker build not yet implemented"

docker-run: ## Run Docker container
	@echo "Docker run not yet implemented"

# Utility targets
info: ## Show project information
	@echo "POM Reader - Maven POM File Parser"
	@echo "Python version: $(shell python3 --version)"
	@echo "Pip version: $(shell pip --version)"
	@echo "Project version: $(shell make version)"

deps: ## Show installed dependencies
	pip list

deps-outdated: ## Show outdated dependencies
	pip list --outdated

update-deps: ## Update development dependencies
	pip install --upgrade -e ".[dev]"

# Quick development cycle
quick: format lint test ## Quick development cycle (format, lint, test)

# Virtual environment detection and usage
VENV_PYTHON = .venv/bin/python3
VENV_PIP = .venv/bin/pip
HAS_VENV = $(shell test -d .venv && echo "yes" || echo "no")
IS_VENV_ACTIVE = $(shell test -n "$$VIRTUAL_ENV" && echo "yes" || echo "no")

# Use virtual environment Python if available and active, otherwise use system Python
PYTHON = $(shell if [ -n "$$VIRTUAL_ENV" ] && [ -f .venv/bin/python3 ]; then echo ".venv/bin/python3"; else echo "python3"; fi)
PIP = $(shell if [ -n "$$VIRTUAL_ENV" ] && [ -f .venv/bin/pip ]; then echo ".venv/bin/pip"; else echo "pip"; fi)

# All-in-one development setup
setup: clean install-venv ## Complete setup with virtual environment
	@echo ""
	@echo "🎉 POM Reader is ready for development!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate the virtual environment:"
	@echo "     source .venv/bin/activate"
	@echo "  2. Run tests to verify:"
	@echo "     make test"
	@echo ""
	@echo "Quick commands (after activating venv):"
	@echo "  make run          - Run the example"
	@echo "  make test         - Run tests"
	@echo "  make format       - Format code"
	@echo "  make lint         - Lint code"
	@echo "  make cli-test     - Test CLI commands"
	@echo "  make clean        - Clean build artifacts"

setup-system: clean install-dev test cli-test ## Complete setup in system Python
	@echo ""
	@echo "🎉 POM Reader is ready for development!"
	@echo ""
	@echo "Quick commands:"
	@echo "  make run          - Run the example"
	@echo "  make test         - Run tests"
	@echo "  make format       - Format code"
	@echo "  make lint         - Lint code"
	@echo "  make cli-test     - Test CLI commands"
	@echo "  make clean        - Clean build artifacts"

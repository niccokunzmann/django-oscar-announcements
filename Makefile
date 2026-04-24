VENV   := .venv
PYTHON := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

.PHONY: test clean

.venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade setuptools
	$(PIP) install --upgrade distribute
	$(PIP) install -e .[dev]
	$(VENV)/bin/pre-commit install

## test: run the package test suite
test: .venv
	$(PYTEST) tests/ -v

## clean: remove venv and compiled files
clean:
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

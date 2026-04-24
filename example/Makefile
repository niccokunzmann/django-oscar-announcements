VENV   := .venv
PYTHON := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
MANAGE := $(PYTHON) manage.py

.PHONY: run superuser test clean

.venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(MANAGE) migrate
	$(MANAGE) loaddata fixtures/initial.json 2>/dev/null || true
	@echo ""
	@echo "Setup complete."
	@echo "  Create a superuser:  make superuser"
	@echo "  Start the server:    make run"

run: .venv
	$(MANAGE) runserver

superuser: .venv
	$(MANAGE) createsuperuser

test: .venv
	$(MANAGE) check

clean:
	rm -rf $(VENV) db.sqlite3
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv install test test-chat run-sync run-api clean

help:
	@echo "Available targets:"
	@echo "  make venv       Create the local virtual environment"
	@echo "  make install    Install dependencies into .venv"
	@echo "  make test       Run the full unittest suite"
	@echo "  make test-chat  Run chat route tests only"
	@echo "  make run-sync   Run the synchronous example script"
	@echo "  make run-api    Run the async FastAPI example"
	@echo "  make clean      Remove Python cache files"

venv:
	python3 -m venv .venv

install:
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests -p 'test*.py'

test-chat:
	$(PYTHON) -m unittest tests/test_chat_routes.py

run-sync:
	$(PYTHON) tests/run_sync_test.py

run-api:
	$(PYTHON) tests/run_async_api.py

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +

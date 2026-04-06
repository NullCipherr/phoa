PYTHON ?= python
VENV ?= .venv
VPY := $(VENV)/bin/python
VPIP := $(VENV)/bin/pip

.PHONY: setup install-dev lint test run run-web
.PHONY: docker-build docker-run-cli docker-run-web docker-compose-web docker-compose-cli

setup:
	$(PYTHON) -m venv $(VENV)
	$(VPIP) install --upgrade pip
	$(VPIP) install -e .[dev]

install-dev:
	$(VPIP) install -e .[dev]

lint:
	$(VENV)/bin/ruff check .

test:
	$(VENV)/bin/pytest

run:
	$(VPY) main.py

run-web:
	$(VENV)/bin/streamlit run streamlit_app.py

docker-build:
	docker build -t phoa:latest .

docker-run-cli:
	docker run --rm phoa:latest python main.py --no-viz --steps 120

docker-run-web:
	docker run --rm -p 8501:8501 phoa:latest streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501

docker-compose-web:
	docker compose up --build phoa-web

docker-compose-cli:
	docker compose --profile cli up --build phoa-cli

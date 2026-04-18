SHELL := /bin/bash

PYTHON := python3
VENV_DIR := backend/venv
PIP := $(VENV_DIR)/bin/pip
UVICORN := $(VENV_DIR)/bin/uvicorn
NPM := npm

.PHONY: venv install backend backend-prod frontend build-frontend run clean reset reinstall

venv:
	bash scripts/create_venv.sh

install: venv
	bash scripts/install.sh

backend:
	bash scripts/run_backend.sh

backend-prod:
	bash scripts/run_backend_prod.sh

frontend:
	bash scripts/run_frontend.sh

build-frontend:
	cd frontend && npm run build

run:
	bash scripts/bootstrap.sh

clean:
	bash scripts/clean.sh

reset:
	bash scripts/reset.sh

reinstall: reset install

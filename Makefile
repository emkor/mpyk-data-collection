config: clean setup install
all: ut build
redeploy: remote-stop remote-clean upload remote-start

PY3 = python3
VENV = .venv/$(shell basename $$PWD)
VENV_PY3 = .venv/$(shell basename $$PWD)/bin/python3
REMOTE_HOST ?= "rpi4b"
REMOTE_DIR ?= "/home/ubuntu/mpyk"
REMOTE_DATA_DIR ?= "/mnt/storage/mpyk"

clean:
	@echo "---- Doing cleanup ----"
	@rm -rf .venv
	@mkdir -p .venv

setup:
	@echo "---- Setting up virtualenv ----"
	@$(PY3) -m venv $(VENV)
	@echo "---- Installing dependencies and app itself in editable mode ----"
	@$(VENV_PY3) -m pip install --upgrade pip wheel setuptools

install:
	@echo "---- Installing package in virtualenv ---- "
	@$(VENV_PY3) -m pip install -r src/requirements.txt
	@$(VENV_PY3) -m pip install -r src/requirements-dev.txt

ut:
	@echo "---- Running unit tests ---- "
	@$(VENV_PY3) -m pytest -ra -v -s src/test_unit.py

at:
	@echo "---- Running acceptance tests ---- "
	@$(VENV_PY3) -m pytest -ra -v -s src/test_data_availability.py

build:
	@echo "---- Building Docker image ---- "
	@docker build -t "mpyk-data-collection:latest" ./src

run-dev:
	@echo "---- Running Docker image ---- "
	@mkdir -p tmp/csv tmp/zip
	@docker run --rm --name "mpyk" -v "${PWD}/tmp/csv:/mpyk/csv" -v "${PWD}/tmp/zip:/mpyk/zip" "mpyk-data-collection:latest"

clean-run:
	@echo "---- Removing artifacts ---- "
	@sudo rm -rf tmp/csv/* tmp/zip/*

remote-clean:
	@echo "---- Cleaning remote directory ----"
	@ssh $(REMOTE_HOST) "docker-compose -f $(REMOTE_DIR)/docker-compose.yml down" || true
	@ssh $(REMOTE_HOST) "sudo rm -rf $(REMOTE_DIR)"

upload:
	@echo "---- Deploying file artifacts ---- "
	@ssh $(REMOTE_HOST) "mkdir -p $(REMOTE_DIR) $(REMOTE_DATA_DIR)/csv $(REMOTE_DATA_DIR)/zip"
	@scp -C -r src $(REMOTE_HOST):$(REMOTE_DIR)
	@scp -C docker-compose.yml $(REMOTE_HOST):$(REMOTE_DIR)

remote-build:
	@echo "---- Building on remote ---- "
	@ssh $(REMOTE_HOST) "docker-compose -f $(REMOTE_DIR)/docker-compose.yml build"

remote-start:
	@echo "---- Starting on remote ---- "
	@ssh $(REMOTE_HOST) "docker-compose -f $(REMOTE_DIR)/docker-compose.yml up -d"

remote-stop:
	@echo "---- Stopping on remote ---- "
	@ssh $(REMOTE_HOST) "docker-compose -f $(REMOTE_DIR)/docker-compose.yml stop" || true


.PHONY: all config test build clean setup install lint ut at

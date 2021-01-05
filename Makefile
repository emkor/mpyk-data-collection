config: clean setup install
all: ut build

PY3 = python3
VENV = .venv/$(shell basename $$PWD)
VENV_PY3 = .venv/$(shell basename $$PWD)/bin/python3

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

ut:
	@echo "---- Running unit tests ---- "
	@$(VENV_PY3) -m pytest -ra -v -s src/test_unit.py

at:
	@echo "---- Running acceptance tests ---- "
	@$(VENV_PY3) -m pytest -ra -v -s src/test_data_availability.py

build:
	@echo "---- Building Docker image ---- "
	@docker build -t "mpyk-data-collection:latest" ./src

run:
	@echo "---- Running Docker image ---- "
	@mkdir -p tmp/csv tmp/zip
	@docker run --rm --name "mpyk" -v "${PWD}/tmp/csv:/mpyk/csv" -v "${PWD}/tmp/zip:/mpyk/zip" "mpyk-data-collection:latest"

clean-run:
	@echo "---- Removing artifacts ---- "
	@sudo rm -rf tmp/csv/* tmp/zip/*

.PHONY: all config test build clean setup install lint ut at

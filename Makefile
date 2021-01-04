config: clean setup install
test: at
all: test build

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
	@$(VENV_PY3) -m pip install -r requirements.txt

at:
	@echo "---- Running acceptance tests ---- "
	@$(VENV_PY3) -m pytest -ra -v -s test

build:
	@echo "---- Building Docker image ---- "
	@docker build -t "mpyk-data-collection:latest" .

.PHONY: all config test build clean setup install lint ut at

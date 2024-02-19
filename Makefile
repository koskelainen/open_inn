.PHONY: help install reinstall remove run dotenv clean clean-build clean-pyc clean-test test lint/flake8 lint/black
.DEFAULT_GOAL := help

PROJECT_FPATH := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME := $(shell basename $(PROJECT_FPATH))
SHELL := /bin/bash
HOSTNAME := 0.0.0.0
PORT := 8080
DOTENV := .env
PYTHONPATH := $(PROJECT_FPATH)/src/app/
CONDA_ENV_NAME := open_inn
CONDA_VENV_FPATH := environment_dev.yml

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+\/?[a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

ifeq (,$(shell which conda))
    HAS_CONDA=False
else
    HAS_CONDA=True
    ENV_DIR=$(shell conda info --base)
    CONDA_ROOT=$(shell conda info --root)
    CONDA_BIN=$(CONDA_ROOT)/bin/conda
    CONDA_ENV_FPATH=$(ENV_DIR)/envs/$(CONDA_ENV_NAME)
    MY_ENV_DIR=$(ENV_DIR)/envs/
    CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
endif

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

install: dotenv ## create conda venv and install dependencies from $(CONDA_VENV_FPATH)
ifeq (True,$(HAS_CONDA))
	@[ -d "$(CONDA_ENV_FPATH)" ] && \
		echo ">>> Found '$(CONDA_ENV_NAME)' environment in '$(MY_ENV_DIR)'. Skipping installation..." || \
		{ echo ">>> Detected conda, but '$(CONDA_ENV_NAME)' is missing in '$(ENV_DIR)'. Installing ..."; \
		 conda env create -f $(CONDA_VENV_FPATH) -n $(CONDA_ENV_NAME) }
else
	@echo ">>> Install conda first."
	exit
endif

reinstall: remove ## remove conda venv <name_venv> and reinstall dependencies from environment.yml
	conda env create -f $(CONDA_VENV_FPATH) -n $(CONDA_ENV_NAME) -y

remove:  ## remove conda venv <name_venv>
	@[ ! -d "$(CONDA_ENV_FPATH)" ] && \
	echo ">>> Not found '$(CONDA_ENV_NAME)' environment in '$(MY_ENV_DIR)'." || \
	conda remove --name $(CONDA_ENV_NAME) --all -y

run:  ## uvicorn main:app --reload --host <hostname> --port <port>
	source $(CONDA_ROOT)/bin/activate $(CONDA_ENV_NAME) && \
	PYTHONPATH=$(PYTHONPATH) uvicorn main:app --reload --host $(HOSTNAME) --port $(PORT)

dotenv:  ## make .env file from template .env_example
	@if [[ ! -e  $(DOTENV) ]]; then \
		cp .env_example  $(DOTENV); \
	fi

clean: clean/build clean/pyc clean/test  ## remove all build, test, coverage and Python artifacts
	find . -name 'Thumbs.db' -exec rm -rf {} \;
	rm -rf .cache
	rm -rf docs/_build

clean/build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean/pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean/test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint/flake8: ## check style with flake8
	flake8 $(PROJECT_FPATH)/src/app
lint/black: ## check style with black
	black --check $(PROJECT_FPATH)/src/app

lint: lint/flake8 lint/black ## check style

test:  ## run tests with the conda venv python
	source $(CONDA_ROOT)/bin/activate $(CONDA_ENV_NAME) && \
 		pytest src/tests -vv --show-capture=all

tests: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source $(PROJECT_FPATH) -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/$(PROJECT_NAME).rst
	rm -f docs/modules.rst
	source $(CONDA_ROOT)/bin/activate $(CONDA_ENV_NAME) && \
	sphinx-apidoc -o docs/ src/app
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	source $(CONDA_ROOT)/bin/activate $(CONDA_ENV_NAME) && \
	python setup.py sdist && \
	python setup.py bdist_wheel && \
	ls -l dist

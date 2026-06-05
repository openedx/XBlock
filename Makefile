# Do things in edx-platform
.PHONY: clean docs help package quality requirements test upgrade validate

.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
    from urllib import pathname2url
except:
    from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

quality: ## check coding style with pycodestyle and pylint
	pycodestyle
	pylint xblock

validate: test

test: ## run tests on every supported Python/Django combination
	tox

docs: ## generate Sphinx HTML documentation, including API docs
	tox -e docs
	$(BROWSER) docs/_build/html/index.html

requirements: ## install development environment requirements
	uv sync --group dev

upgrade: ## update the uv.lock to use the latest releases satisfying our constraints
	uv run --with edx-lint edx_lint write_uv_constraints pyproject.toml
	uv lock --upgrade

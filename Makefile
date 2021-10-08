# Do things in edx-platform
.PHONY: clean docs help package quality requirements test upgrade

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

test: ## run tests on every supported Python/Django combination
	tox

docs: ## generate Sphinx HTML documentation, including API docs
	tox -e docs
	$(BROWSER) docs/_build/html/index.html

requirements: ## install development environment requirements
	pip install -qr requirements/dev.txt --exists-action w
	pip install -e .

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the pip requirements files to use the latest releases satisfying our constraints
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	pip-compile -v --upgrade --rebuild -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile -v --upgrade --rebuild -o requirements/base.txt requirements/base.in
	pip-compile -v --upgrade --rebuild -o requirements/django.txt requirements/django.in
	pip-compile -v --upgrade --rebuild -o requirements/test.txt requirements/test.in
	pip-compile -v --upgrade --rebuild -o requirements/doc.txt requirements/doc.in
	pip-compile -v --upgrade --rebuild -o requirements/ci.txt requirements/ci.in
	pip-compile -v --upgrade --rebuild -o requirements/dev.txt requirements/dev.in
	# Let tox control the Django version for tests
	sed '/^[dD]jango==/d' requirements/test.txt > requirements/test.tmp
	mv requirements/test.tmp requirements/test.txt

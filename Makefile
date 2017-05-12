quality:
	pep8
	script/max_pylint_violations
	pylint --py3k xblock

package:
	python setup.py register sdist upload

test:
	tox -e py27,py35

docs:
	tox -e docs

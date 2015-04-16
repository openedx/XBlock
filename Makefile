test:
	tox

docs:
	cd doc && make html

quality:
	pep8 --exclude=.tox
	script/max_pylint_violations

package:
	python setup.py register sdist upload

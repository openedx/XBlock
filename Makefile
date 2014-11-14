test:
	coverage run -m nose

docs:
	cd doc && make html

quality:
	pep8
	script/max_pylint_violations

package:
	python setup.py register sdist upload
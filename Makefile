test:
	tox

docs:
	cd doc && make html

quality:
	tox -e py27-quality py35-quality

package:
	python setup.py register sdist upload

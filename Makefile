.PHONY: release


release:
	- rm -rf dist/
	python setup.py bdist sdist
	twine upload dist/* -r pypi-snowball

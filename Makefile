.PHONY: clean-pyc clean-build docs clean lint test coverage docs dist

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"

clean: clean-build clean-pyc
	rm -rf htmlcov/
	rm -rf venv

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr lib/*.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name "__pycache__" -type d -delete

clean-docs:
	rm -f docs/tri*.rst


test:
	pytest

dist: clean
	uv build
	ls -l dist

venv:
	python -m venv venv


makemessages:
	(cd okrand && django-admin makemessages -a)
	(cd examples && django-admin makemessages -a)


compilemessages:
	(cd okrand && django-admin compilemessages)
	(cd examples && django-admin compilemessages)

release:
	rm -rf dist/ build/ && uv build && uv publish

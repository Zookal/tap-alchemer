.DEFAULT_GOAL := test

test:
	pylint tap_alchemer -d missing-docstring
	nosetests tests/unittests

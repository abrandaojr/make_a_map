.PHONY: setup map clean

PYTHON := .venv/bin/python

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -e ".[dev]"

map:
	$(PYTHON) -m make_a_map build legal-amazon

templates:
	$(PYTHON) -m make_a_map templates

test:
	$(PYTHON) -m pytest -q -s

doctor:
	$(PYTHON) -m make_a_map doctor

clean:
	rm -f outputs/legal-amazon/latest/*

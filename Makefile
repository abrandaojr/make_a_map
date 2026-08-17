.PHONY: setup build variations qgis qgis-finalize qgis-validate doctor lint test check

PYTHON := .venv/bin/python

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -e ".[dev]"

build:
	$(PYTHON) -m make_a_map build $(if $(OFFLINE),--offline,)

variations:
	$(PYTHON) -m make_a_map variations

qgis:
	$(PYTHON) -m make_a_map qgis $(if $(OFFLINE),--offline,)

# These targets require the native QGIS Python environment rather than .venv.
qgis-finalize:
	python3 tools/finalize_qgis_projects.py outputs

qgis-validate:
	python3 tools/validate_qgis_projects.py outputs

doctor:
	$(PYTHON) -m make_a_map doctor

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest -q -s

check: lint test

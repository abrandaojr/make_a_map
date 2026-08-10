.PHONY: setup map clean

PYTHON := .venv/bin/python

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

map:
	$(PYTHON) maps/legal_amazon.py

clean:
	rm -f outputs/legal_amazon_pt-BR.* outputs/legal_amazon_en-US.*


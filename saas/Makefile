# Developer shortcuts. Backend tests run in a local venv (Python 3.10+; Docker uses 3.12).
PYTHON ?= $(shell command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)
VENV   ?= backend/.venv
PY     := $(VENV)/bin/python

.PHONY: test test-unit test-acceptance test-spec-report

STAMP := $(VENV)/.deps-installed

$(STAMP): backend/requirements-dev.txt
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q -r backend/requirements-dev.txt
	@touch $(STAMP)

$(PY): $(STAMP)

## Full suite (unit + acceptance + living spec xfails)
test: $(PY)
	cd backend && ../$(PY) -m pytest

test-unit: $(PY)
	cd backend && ../$(PY) -m pytest tests/unit

test-acceptance: $(PY)
	cd backend && ../$(PY) -m pytest -m acceptance

## Show which spec items are still pending (xfail reasons)
test-spec-report: $(PY)
	cd backend && ../$(PY) -m pytest -m acceptance -rxX -q

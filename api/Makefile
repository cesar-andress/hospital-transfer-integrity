PY ?= .venv/bin/python
PIP ?= .venv/bin/pip
STAMP := .venv/.deps-installed

.PHONY: venv install test test-unit test-contract test-acceptance run

$(STAMP): requirements-dev.txt requirements.txt
	python3.12 -m venv .venv
	$(PIP) install -U pip
	$(PIP) install -r requirements-dev.txt
	@touch $(STAMP)

$(PY): $(STAMP)

venv install: $(STAMP)

test: $(PY)
	$(PY) -m pytest

test-unit: $(PY)
	$(PY) -m pytest -m unit

test-contract: $(PY)
	$(PY) -m pytest -m contract

test-acceptance: $(PY)
	$(PY) -m pytest -m acceptance

run: $(PY)
	$(PY) -m uvicorn app.main:app --host 0.0.0.0 --port 8090

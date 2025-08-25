.PHONY: setup lint typecheck test test-unit test-integration test-e2e property fuzz bench coverage mutation security sbom all

VENV?=.venv
PYTHON=$(VENV)/bin/python
PIP=$(PYTHON) -m pip

setup:
python -m venv $(VENV)
$(PIP) install -U pip
$(PIP) install -e .[dev]
$(PYTHON) --version
$(PYTHON) -m pip list

lint:
$(PYTHON) -m ruff .
$(PYTHON) -m bandit -r modules ForgeCore

typecheck:
$(PYTHON) -m mypy modules ForgeCore

test:
$(PYTHON) -m pytest --junitxml=reports/junit/junit.xml

test-unit:
$(PYTHON) -m pytest -m unit --junitxml=reports/junit/unit.xml

test-integration:
$(PYTHON) -m pytest -m integration --junitxml=reports/junit/integration.xml

test-e2e:
$(PYTHON) -m pytest -m e2e --junitxml=reports/junit/e2e.xml

property:
$(PYTHON) -m pytest -m property --junitxml=reports/junit/property.xml

fuzz:
$(PYTHON) -m pytest -m fuzz --junitxml=reports/junit/fuzz.xml

bench:
$(PYTHON) -m pytest -m unit --benchmark-only --benchmark-json=reports/bench/bench.json

coverage:
$(PYTHON) -m pytest --cov=modules --cov=ForgeCore/forgecore --cov-report=xml:reports/coverage/coverage.xml --cov-report=html:reports/coverage/html

mutation:
$(PYTHON) -m mutmut run --paths-to-mutate modules ForgeCore/forgecore --tests-dir tests/unit
$(PYTHON) -m mutmut results > reports/mutation/results.txt
python - <<'PY'
import re,sys
text=open('reports/mutation/results.txt').read()
match=re.search(r'mutation score \(([0-9.]+)%\)', text)
score=float(match.group(1)) if match else 0
print(f'Mutation score: {score}%')
if score < 60:
    sys.exit(1)
PY

security:
$(PYTHON) -m pip_audit -r requirements.txt -f reports/security/audit.json || true
gitleaks detect --source . --report-path reports/security/gitleaks.json || true

sbom:
cyclonedx-bom -o reports/sbom/bom.json

all: lint typecheck test coverage security

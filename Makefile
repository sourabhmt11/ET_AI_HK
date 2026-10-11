.PHONY: setup test lint typecheck guards eval ci clean docs

setup:
	pip install -e ".[dev,all]"
	pre-commit install

test:
	pytest

test-verbose:
	pytest -v --tb=long

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

typecheck:
	mypy src/

# REP-07 and REP-09 guards: an old name or a drifted version fails here
# as well as in CI, so a contributor finds out before pushing.
guards:
	python tools/check_old_names.py
	python tools/check_version_sync.py

# EVL-02: the evaluation command on the shipped default configuration.
eval:
	python -m cosmac eval run --set docs/cosmac/evidence/probe_set_v1.jsonl --out eval-out

ci: lint typecheck guards test

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build *.egg-info

docs:
	mkdocs serve

docs-build:
	mkdocs build

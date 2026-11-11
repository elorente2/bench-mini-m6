PYTHON := $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)

.PHONY: help bootstrap test lint fmt check report engines run-splash run-mirai run-ollama run-all eval eval-report clean

help:
	@echo "make bootstrap   create .venv and install dev dependencies"
	@echo "make test        run unit tests"
	@echo "make lint        run ruff check and format check"
	@echo "make fmt         auto-fix lint and formatting"
	@echo "make check       lint + test"
	@echo "make engines     list configured engines"
	@echo "make run-splash  measure Splash (engine must already be running)"
	@echo "make run-mirai   measure Mirai/uzu (engine must already be running)"
	@echo "make run-all     start, measure and stop every engine, then report"
	@echo "make report      regenerate reports/latest.md from results/*.json"
	@echo "make eval        run the accuracy suite: make eval ENGINE=<label>"
	@echo "make eval-report regenerate reports/eval-latest.md from results/eval/*.json"

bootstrap:
	./scripts/bootstrap.sh

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

fmt:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

check: lint test

report:
	$(PYTHON) -m bench.cli report results/*.json --out reports/latest.md

engines:
	$(PYTHON) -m bench.cli engines

run-splash:
	$(PYTHON) -m bench.cli run splash

run-mirai:
	$(PYTHON) -m bench.cli run mirai

run-ollama:
	$(PYTHON) -m bench.cli run-all --engines ollama-q3kxl,ollama-default --report

run-all:
	$(PYTHON) -m bench.cli run-all --report

eval:
	$(PYTHON) -m bench.cli eval $(ENGINE)

eval-report:
	$(PYTHON) -m bench.cli eval-report results/eval/*.json --out reports/eval-latest.md

clean:
	rm -rf .pytest_cache .ruff_cache logs .run

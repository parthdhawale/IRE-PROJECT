# One command per phase. Run `make setup` once, then `make data && make test`.
PY ?= .venv/bin/python

.PHONY: setup data stats test sections baselines figures clean-cache

setup:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

data:
	$(PY) scripts/download_data.py
	$(PY) scripts/build_corpus_stats.py

stats:
	$(PY) scripts/build_corpus_stats.py

test:
	$(PY) -m pytest -q

sections:
	$(PY) scripts/build_sections.py

SPLIT ?= mini
baselines:
	$(PY) scripts/run_baselines.py --split $(SPLIT)

figures:
	$(PY) scripts/plot_baselines.py --split $(SPLIT)

clean-cache:
	rm -rf data/cache/*

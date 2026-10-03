PY := .venv/bin/python
DBT := .venv/bin/dbt

.PHONY: all setup data build report clean

all: data build report

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

data:
	$(PY) generator/generate.py

build:
	$(DBT) build --profiles-dir .

report:
	$(PY) analyses/fee_pilot_readout.py > /dev/null
	@echo "Wrote reports/findings.json, reports/figures/, exports/"

clean:
	rm -rf target logs warehouse.duckdb data/raw/*.parquet

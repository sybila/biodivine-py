# Development entry points. Every target runs in the virtual environment in `.venv`.
.PHONY: help venv develop test coverage lint docs verify

VENV ?= $(CURDIR)/.venv
PYTHON := $(VENV)/bin/python

# macOS 27's loader rejects extension modules processed by the system `strip` ("mis-aligned
# LINKEDIT string pool"), which the release profile runs by default; development builds are
# therefore not stripped. Published wheels are built by CI and are not affected.
DEVELOP_ENV := CARGO_PROFILE_RELEASE_STRIP=none VIRTUAL_ENV=$(VENV)

help:
	@echo "make venv      create .venv with the build, test and documentation tools"
	@echo "make develop   build biodivine-sys into .venv and install biodivine in editable mode"
	@echo "make test      run the Rust and the Python test suites"
	@echo "make coverage  run the Python test suite with coverage (report in coverage.xml)"
	@echo "make lint      cargo fmt --check, cargo clippy (warnings denied), ruff"
	@echo "make docs      build the API reference of the biodivine package"
	@echo "make verify    run every check above"

venv:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install maturin pytest pytest-cov ruff -r biodivine/docs/requirements.txt

develop:
	cd biodivine-py-sys && $(DEVELOP_ENV) $(VENV)/bin/maturin develop --release
	$(PYTHON) -m pip install --no-deps -e biodivine

test:
	cargo test --workspace
	$(PYTHON) -m pytest biodivine

# Line and branch coverage of the pure-Python package by its test suite (configured in
# `biodivine/pyproject.toml`), printed and written to coverage.xml, which CI uploads to Codecov.
coverage:
	$(PYTHON) -m pytest biodivine --cov --cov-config=biodivine/pyproject.toml \
		--cov-report=term --cov-report=xml:coverage.xml

lint:
	cargo fmt --check
	cargo clippy --workspace --all-targets -- -D warnings
	$(VENV)/bin/ruff check biodivine scripts

docs:
	rm -rf biodivine/docs/_build
	$(PYTHON) -m sphinx -W -b html biodivine/docs biodivine/docs/_build

verify: lint develop test docs
	RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --workspace
	cargo +1.95.0 test --workspace

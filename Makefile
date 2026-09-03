PYTHON ?= .venv/bin/python
IMAGE ?= ihv-cenic-chirpstack-devices:0.2.2

.PHONY: all format lint test docker-build docker-smoke

all: lint test docker-build docker-smoke

format:
	$(PYTHON) -m ruff format app tests

lint:
	$(PYTHON) -m ruff format --check app tests
	$(PYTHON) -m ruff check app tests

test:
	$(PYTHON) -m pytest -W error

docker-build:
	docker build --tag $(IMAGE) .

docker-smoke:
	docker run --rm $(IMAGE) --help >/dev/null

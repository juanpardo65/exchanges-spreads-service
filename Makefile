.PHONY: run test install docker-build docker-up docker-up-full postgres

run:
	./run.sh

test:
	uv run pytest
	# or: pytest

install:
	uv sync --all-extras
	# or: pip install -e ".[dev]"

docker-build:
	docker build -t spreads .

docker-up:
	docker compose up -d postgres

docker-up-full:
	docker compose --profile full up -d

postgres:
	docker compose up -d postgres

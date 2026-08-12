.PHONY: install api web test lint format check

install:
	uv sync --extra dev

api:
	uv run uvicorn apps.api.main:app --reload

web:
	uv run streamlit run apps/web/Home.py

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

check:
	uv run ruff check .
	uv run pytest
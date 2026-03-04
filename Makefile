.PHONY: lint test build clean

lint:
	python -m ruff check src tests
	python -m mypy src

test:
	python -m pytest

build:
	python -m build

clean:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache
	rm -rf src/*.egg-info src/framescribe.egg-info
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +

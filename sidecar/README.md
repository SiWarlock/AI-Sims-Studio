# Sidecar

Python 3.12 sidecar for AI Sims Creator. See `CLAUDE.md` in this directory
for the full architecture and conventions.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

## Common commands

```bash
ruff check .
ruff format .
mypy --strict .
pytest -q
pytest -q -m integration
pytest --cov
```

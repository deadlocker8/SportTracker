poetry run ruff check --fix
poetry run ruff format
poetry run mypy sporttracker tests
poetry run bandit -r . -c .\pyproject.toml
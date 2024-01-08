# SportTracker

Self-hosted sport data tracking server.

![](/src/static/images/SportTracker.png)

## Run SportTracker

1. Install dependencies via `poetry install --no-root`
2. Copy `settings-example.json` to `settings.json` and adjust your to your configuration
3. Run the server: `<path_to_python_executable_in_poetry_venv src\SportTracker.py` 

Or use the docker image.

## Command line arguments
- `--debug`, `-d` = Enable debug mode
- `--dummy`, `-dummy` = Generate dummy tracks and user

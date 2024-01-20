# SportTracker

Self-hosted sport data tracking server.

<img src="src/static/images/SportTracker.png" alt="drawing" width="150" height="150"/>

## Key Features

### Multi-user support
Multiple users can track their sport data using different accounts.

### Record your sport data
Record the data of your training sessions after you have finished them.

Supported types of sports:
- Biking
- Running

You can fill in a lot of information for each training session. If the pre-defined inputs are not enough, it is possible to set custom fields for each type of sports.

### Month goals
Set custom month goals (either distance or number of tracks).
The current status of each month goal is visualized via progress bars.

### GPX tracks / Map
A GPX recoding can be attached to every single track. The GPX recordings can be viewed on a map.

### Charts
Tracked data is visualized in charts, e.g.:
- Distance per month
- Average speed
- Duration per Track
- etc.

### Achievements
The achievement page shows aggregated information about all your tracks.

### Available languages
- German
- English


## Run SportTracker
1. Install dependencies via `poetry install --no-root`
2. Copy `settings-example.json` to `settings.json` and adjust to your configuration
3. Run the server: `<path_to_python_executable_in_poetry_venv> src/SportTracker.py` 

💡 Or use the docker image.

## Command line arguments
- `--debug`, `-d` = Enable debug mode
- `--dummy`, `-dummy` = Generate dummy tracks and demo user


## This project uses 3rd-party components

### Python dependencies
Python dependencies can be found in `pyproject.toml` and corresponding `poetry.lock`.

### Javascript / CSS dependencies
- Bootstrap https://getbootstrap.com/
- Leaflet https://leafletjs.com/
- Mousetrap https://craig.is/killing/mice

### Additional dependencies
- Google Material Icons https://fonts.googleapis.com/icon?family=Material+Icons

### Icons / Images
- bike icon by Google Material Icons https://fonts.google.com/icons?selected=Material%20Icons%3Adirections_bike%3A
- runner icon by Google Material Icons https://fonts.google.com/icons?selected=Material%20Icons%3Adirections_run%3A
- checklist icon by Freepik - Flaticon https://www.flaticon.com/de/kostenlose-icons/hakchen
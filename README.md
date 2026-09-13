# SportTracker

SportTracker is a self-hosted server for recording and analyzing your workout data. All data stays on your own server, fully under your control.

<img src="sporttracker/static/images/SportTracker.png" alt="drawing" width="150" height="150"/>

## Key Features

### Multi-user support
SportTracker supports multiple users. Each user registers with their own account, so everyone's workout data stays completely separate.

### Record your workout data
Log your completed workouts and capture detailed information for every session.

Supported workout types:

- Distance-based: Biking, Running, Hiking
- Duration-based: Fitness Workouts

Every workout comes with a rich set of standard input fields and if those are not enough, you can define custom fields per workout type. 

Workouts can also be shared via public links.

![](docs/screenshots/tracks.png)

### Month goals
Set monthly goals for distance, duration or number of workouts and track your progress toward each goal on a live progress bar.

![](docs/screenshots/goals.png)

### Heart rate data
Add heart rate data to any workout via the SportTracker API and view it as a chart.
![](docs/screenshots/heart_rate_chart.png)

### GPX tracks / Map
Attach a GPX recording to any distance-based workout and view your tracks on a map. Either all tracks in a single overview or one track at a time with additional details.

View all GPX tracks on a map:
![](docs/screenshots/map_all.jpg)

View a single GPX track with additional details (e.g. the track line colored by speed):
![](docs/screenshots/map_single.jpg)

### FIT tracks
SportTracker also supports Garmin `.fit` files in addition to GPX. When you upload a `.fit` file for a workout or a planned tour, a GPX file is automatically generated and both files are stored in the `data` folder.

__NOTE__: The generated GPX file only contains basic data like latitude, longitude, timestamps and altitude information.

#### Use FIT files to prefill the workout form
You can also use a `.fit` file to automatically prefill the workout form, e.g. duration, distance, and other values are taken directly from the file.

### Tile Hunting
Tile hunting divides the world map into roughly same-sized tiles and allows you to track which of those tiles you already visited.
Each user can enable it optionally.
If enabled, an additional map shows all tiles you have already visited. A tile is considered visited as soon as at least one GPX track crosses it. By default, a tile matches an OpenStreetMap tile at zoom level 14 (configurable in the SportTracker settings file).

Tile hunting is a great way to discover new areas or to stay motivated to explore new routes. The map also highlights the largest square area that is completely covered by your visited tiles.

Overall tile hunting map:
![](docs/screenshots/tile_hunting_map.jpg)

Map for a single workout:
![](docs/screenshots/tile_hunting_single.jpg)

#### Tile hunting overlay access
To plan your next tile hunting route you may want to allow access to your tile hunting map via a share code in your user settings.  
This can be useful to add a custom overlay to OpenStreetMap based maps, e.g. https://bikerouter.de.

1. Add a custom overlay layer
2. Use the url shown on your user settings page (e.g. http://localhost/map/tileOverlay/1df60cca70c340239cfd869673443be4/{z}/{x}/{y}.png)

__NOTE__: In your user settings, you can choose whether tiles that are visited by your already planned tours should be displayed (in grey) in the overlay.

### Tile Hunting heatmap
In addition to the normal tile hunting map a heatmap is available. Each tile is colored according to the number of workouts visiting it, and you can click on a tile to get the exact number of visits.

Tile hunting heatmap:
![](docs/screenshots/tile_hunting_heatmap.jpg)

### Charts
Tracked data is visualized in charts, for example:
- Distance per month
- Average speed
- Duration per workout
- and more

Example charts:
![](docs/screenshots/chart_calendar.png)
![](docs/screenshots/chart_duration_per_track.png)
![](docs/screenshots/chart_distance_per_month.png)

### Annual Statistics
Each year is summarized for every workout type, giving you a quick overview of your progress over time.

![](docs/screenshots/annual_statistics_1.png)
![](docs/screenshots/annual_statistics_2.png)


### Achievements
The achievement page shows aggregated information about all your workouts.

![](docs/screenshots/achievements.png)

### Maintenance Events
Record your maintenance events for each workout type.  
You can optionally set reminders for each maintenance.  
SportTracker can be configured to send notifications via a ntfy server once a maintenance reminder is triggered.

![](docs/screenshots/maintenance.png)

### Planned Tours
Plan and save routes for distance-based workout types and view them on a map. Once you have actually completed a planned tour, you can link the corresponding workout to it.

![](docs/screenshots/planned_tours.jpg)

Share planned tours with other SportTracker users or create public links.
![](docs/screenshots/shared_planned_tour.jpg)


### Long-distance Tours (tours with multiple stages)
Combine multiple planned tours into a long-distance tour and treat them as stages.  
Track your progress on how many stages you have already completed and use the overview map to prepare for upcoming stages.

![](docs/screenshots/long_distance_tour.jpg)

#### Enable GPX preview Images

SportTracker can show a preview image for each planned tour and long-distance tour. The images are not generated by SportTracker.  
An external service (GpxToImageRenderer) can be used instead.

To activate GPX preview images, follow these steps:

**1. Set up a GpxToImageRenderer instance** (https://github.com/deadlocker8/GpxToImageRenderer)
- a) Build the docker image: `docker build -t gpxtoimagerenderer .`
- b) Run the docker image: `docker run -p 3000:3000 gpxtoimagerenderer`
- Or, if you use docker compose, see `docker-compose-with-gpxtoimagerenderer.yaml` and adjust it according to the section `How to run SportTracker via docker compose`.

**2. Enable GPX preview images in your SportTracker settings.json**
Update the section `gpxPreviewImages` in your `settings.json` to contain the following values:
```json
"gpxPreviewImages": {
    "enabled": false,
    "url": "http://localhost:3000",
    "timeout": 30,
    "width": 800,
    "height": 450,
    "dpi": 100,
    "lineWidth": 3,
    "lineColor": "#1267FF",
    "padding": 0.1,
    "basemap": "osm",
    "format": "jpeg",
    "quality": 85,
    "userAgent": "MyUserAgent"
}
```
`http://localhost:3000` is the address and port of your GpxToImageRenderer instance from step 1.
`MyUserAgent` is an arbitrary string identifying your GpxToImageRenderer instance. Necessary to comply with the OpenStreetMap tile server usage policy.


### Notifications
SportTracker creates several notifications on certain events:

- a maintenance reminder limit is exceeded
- planned tours:
  - a planned tour is shared with you
  - a shared planned tour has been updated
  - your access to a shared planned tour has been revoked
  - a shared planned tour has been deleted
- long-distance tours:
  - a long-distance tour is shared with you
  - a shared long-distance tour has been updated
  - your access to a shared long-distance tour has been revoked
  - a shared long-distance tour has been deleted
- a workout sets a new distance record for its workout type
- a fitness workout sets a new duration record
- a month goal is reached
- the total distance of a month is greater than any previous month
- the total duration of a month is greater than any previous month

All notifications are shown in the notification center (reachable via the notification counter in the navbar).
SportTracker can also be configured to send these notifications via a notification provider.

Supported notification providers:
- `ntfy` (more information about ntfy and how to set up your own ntfy server: https://github.com/binwiederhier/ntfy)

![](docs/screenshots/notifications.jpg)

For each notification provider, you can choose which notifications should be sent:
![](docs/screenshots/notifications_settings.jpg)


### Body Weight
Track your body weight over time.
You can add, edit and delete weight entries and each entry shows the change compared to the previous entry.
The overview page shows statistics (latest, average, min and max weight), a chart of your weight over time and your body mass index (BMI).

![](docs/screenshots/body_weight.png)

### Available languages
- German
- English


## API
SportTracker exposes a REST API for the most common use cases.  
Interactive API documentation (Swagger UI) is available at `/api/v2/docs`.


## How to run SportTracker locally
1. Install dependencies via `poetry install --no-root --without dev`
2. Run `npm install` and `npm run build` inside the `js` folder.
3. Copy `settings-example.json` to `settings.json` and adjust to your configuration
4. Run the server: `<path_to_python_executable_in_poetry_venv> src/SportTracker.py` 

## Command line arguments
- `--debug`, `-d` = Enable debug mode
- `--dummy`, `-dummy` = Generate dummy workouts and demo user

## How to run SportTracker via docker compose
An example docker compose file is provided (`docker-compose.yaml`).

You have to make the following changes before starting via docker compose:
1. In the `docker-compose.yaml` change `<POSTGRES_DB_NAME>`, `<POSTGRES_USER>` and `<POSTGRES_PASSWORD>`.
2. The `docker-compose.yaml` uses volume mounts to persist your data even if the containers are stopped and removed.
  - Therefore, you have to change `<PATH_ON_HOST>` to an absolute path to a folder on your host machine.
3. Copy `settings-example.json` to `<PATH_ON_HOST>/settings.json` and adjust to your configuration. 
  - It is important to change the value of `secret`. 
  - Adjust the database URI and set `sporttracker-user`, `sporttracker-password` and `sporttracker-db-name` to match the values in the `docker-compose.yaml` from step 1.
4. Build and run all containers using `docker compose up --build`.
5. Observe the console output for the admin password that is generated only once during the initialization of the SportTracker container.
6. Stop all containers.
7. Set the correct ownership for the folder `<PATH_ON_HOST>/data` by running `sudo chown -R 20000:20000 <PATH_ON_HOST>/data`, where `20000` is the user id set in the `docker-compose.yaml`.
8. Start all containers via `docker compose up -d`
9. You should be able to access SportTracker on localhost:10022
10. Login via username `admin` and the password from the console output.
11. Create a new user and login as this user.

## Database migration
Updating to the latest SportTracker release may require database migration.   
This is only necessary if you already have a running SportTracker instance and a database filled with entries.  
Whether a database migration is necessary will be stated in the release notes.  
The migration will be performed automatically upon start of SportTracker.


## This project uses 3rd-party components

### Python dependencies
Python dependencies can be found in `pyproject.toml` and corresponding `poetry.lock`.

### Javascript / CSS dependencies
Javascript dependencies can be found in `js/package.json` and corresponding `js/package-lock.json`. 

### Additional dependencies
- Google Material Symbols https://fonts.google.com/icons
- Font Awesome Icons https://fontawesome.com/
- OpenStreetMap https://www.openstreetmap.org/about

### Icons / Images
- bike icon by Google Material Icons https://fonts.google.com/icons?selected=Material%20Icons%3Adirections_bike%3A
- runner icon by Google Material Icons https://fonts.google.com/icons?selected=Material%20Icons%3Adirections_run%3A
- checklist icon by Freepik - Flaticon https://www.flaticon.com/de/kostenlose-icons/hakchen
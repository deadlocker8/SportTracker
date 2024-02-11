# 1.10.0
- add: new chart: year calendar
- add: api: return id of created track or month goal
- add: new api route to upload a gpx track for an existing track
- add: new api route to fetch all existing tracks
- chore: update dependencies

# 1.9.2
- fix: chart duration per track
- fix: achievement for month goal streak: fix calculation of streak
- ci: added code formatter and linter "ruff"
- ci: added type checker "mypy"

# 1.9.1
- fix: wrong date localization at beginning of year
- fix: achievement for month goal streak: fix calculation of streak
- fix: achievement for month goal streak: current month should be added to streak if all goals are reached even if month is not over yet
- fix: edit track: distance input not prefilled
- fix: add missing grouping separator for large numbers
- chore: update dependencies

# 1.9.0
- add: localize dates, numbers and maps
- chore: update dependencies

# 1.8.0
- add: license, readme and screenshots
- add: dummy data generator
- add: improved chart and track chooser styling

# 1.7.2
- fix: new track page not opening

# 1.7.1
- fix: CORS errors

# 1.7.0
- add: gpx files can be uploaded and attached to a track
- add: gpx files can be viewed on an interactive map
- add: show an elevation chart for gpx tracks on map
- add: show a speed chart for gpx tracks on map
- add: a single gpx track on map will be shown with "hotline" feature (green to red gradient along the track showing the speed)
- add: automatically join multiple track and segments in gpx files to allow them to be shown on map

# 1.6.1
- fix: overlapping data points in chart for average speed
- fix: calculation of month goal streak achievement
- fix: ordering of changelog entries

# 1.6.0
- add: search for tracks by name
- add: jump to month and year after editing/creating a track

# 1.5.1
- fix: improved form input field size for durations
- fix: allow month goals to be created before 2023

# 1.5.0
- add: values shown for each track in track list are now configurable in user settings
- fix: sort case-insensitive
- fix: prevent deletion of admin user

# 1.4.2
- fix: custom field form

# 1.4.1
- fix: track edit page

# 1.4.0
- BREAKING CHANGE: replaced special track classes with single class and custom fields
- add: new chart: average speed (bar chart)
- add: new chart: distance per custom field (pie chart)
- add: new chart: duration per track name
- add: allow bulk creation of month goals
- add: autocomplete for already used track names in new track form
- add: new about page with changelog

# 1.3.0
- fix charts: fill missing years and months
- fix: charts: fixed clipped legend
- fix: charts: cast number to int/float
- fix: deletion of month goals

# 1.2.0
- add: localization for achievements
- add: new chart: distance per bike
- fix: improve date conversion

# 1.1.0
- add: added achievements page
- fix: only show data for current user in charts

# 1.0.0
- initial release
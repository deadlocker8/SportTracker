# 1.35.0 - (XX.XX.XX)
- add: planned tours can now be filtered (#123)
- add: send notifications for maintenance reminders via ntfy (#168)
- add: tile hunting heatmap: new map where each tile will be colored according to the number of workouts that visited each tile (#184)
- add: chart "duration per workout" now also includes fitness workouts (#181)
- add: new chart: duration per month (#180)
- fix: missing y-axis title in all charts
- fix: gpx track download: add name to gpx metadata (#183)

# 1.34.0 - (17.02.25)
- add: new API version v2.1.0
- add: API: improve login/authorization handling (new post route /api/v2/login) (#174)
- add: SportTracker now allows to use .fit files to automatically prefill the workout form with data from the .fit file (e.g. duration, distance, etc.) (#178)
- fix: require fresh login for critical operations (e.g. everything in admin area or change of own password) (#174)
- fix: average heart rate was not shown in form (#177)
- chore: update dependencies (#173)

# 1.33.1 - (08.02.25)
- fix: fix quick filter state (prevents page load with old login session)

# 1.33.0 - (04.02.25)
- BREAKING CHANGE: Big refactoring for cleaner database structure. All data is automatically migrated upon start. (#160)
- BREAKING CHANGE: API v2.0.0 - Complete rewrite of the API (now available at /api/v2) (#166)
- add: workouts: new field to store the workout type (duration-based or repetition-based) (#158)
- add: workouts: new field to store one or more workout categories (arms, legs, core, etc.) (#159)
- add: single workout map: add option to only highlight new visited tiles (#144)
- add: tile hunting map: click on a bar in chart now opens the corresponding workout in a new browser tab (#171)
- add: update icons to google material symbols (#162)
- add: self-host icons (#162)
- fix: annual statistics: show flat trend icon if there was no increase or decrease for a certain value (#157)
- fix: maintenance events for fitness workouts now only show dates and time difference and no distances (#163)
- fix: maintenance reminders are now only allowed for distance-based workouts (#170)
- fix: charts are now shown correctly even if no workouts exist (#169)
- fix: sorting of planned tours (#172)
- chore: update dependencies (#164, #167)
- chore: update georender (#161)

# 1.32.0 - (01.01.25)
- add: maintenance reminders: for each maintenance an optional reminder can be activated. If a maintenance exceeds the given reminder limit you will be notified in the navbar and on the maintenance page (#149)
- add: new track type "Workout" - In addition to the existing distance based track types a new type is now available that is duration based, e.g. for workouts (#152)
- add: new month goal type: duration month goal
- add: add formatted text for distance per year and distance per month chart (#155)
- add: chart: distance per participant: include distance travelled alone (#151)
- fix: add multiple month goals: end month is now included (#148)
- chore: update to python 3.12 (#150)
- chore: update dependencies

# 1.31.0 - (09.11.24)
- add: redesigned maintenance events page (grouped by type and description, show distances, show distance until today, ...) (#141)
- add: achievements page: show date for longest track and link to corresponding track (#146)
- add: tile hunting: new user settings option to allow access to your tile hunting map via share code (#136)
- fix: responsiveness of settings page (#140)
- fix: responsiveness of track form page (#140)
- fix: responsiveness of annual achievements modals (#140)
- fix: tile hunting map: the total number of visited tiles and the bar chart now correctly shows the visited tiles depending on the selected track types and years (#142)
- fix: track map: the elevation chart is now correctly displayed even if the gpx track does not contain elevation information for the first data points (#145)
- chore: update dependencies

# 1.30.0 - (25.09.24)
- BREAKING CHANGE: all uploaded gpx files are now stored in a folder called "data" instead of "uploads". All existing gpx files will be automatically migrated. Please adjust your docker volume mounts.
- add: gpx files are now stored in a zip to reduce file size
- add: planned tour preview images are stored in the same folder as the corresponding gpx file
- add: changed color of save buttons for track and planned tour forms to ensure they are not confused with the "create link" button
- add: improve file name on gpx download
- add: the changelog now also contains the release dates for each version
- add: added support for uploading .fit files for tracks and planned tours
- fix: tile hunting map: the total number of visited tiles and the bar chart now correctly shows the visited tiles depending on the selected track types and years
- chore: update dependencies

# 1.29.0 - (17.09.24)
- BREAKING CHANGE: you must update your settings.json (new section "tileHunting", see settings-example.json)
- add: gpx meta information is calculated only once and stored in database. CAUTION: The first start of SportTracker will take quite some time to calculate the gpx information for all uploaded gpx files.
- add: settings files are checked for missing entries upon server start
- add: tile hunting map (for details see README)
- chore: update dependencies

# 1.28.0 - (09.08.24)
- add: search: add pagination on bottom
- add: show edit button for track and planned tour map
- add: planned tour overview: clicking on number of linked tracks opens a modal with all linked tracks
- add: performance improvement: gpx meta info is calculated only once per gpx track and then cached
- add: delete previous gpx track when new one is uploaded
- chore: update dependencies

# 1.27.0 - (04.08.24)
- add: allow tracks to be linked to a planned tour
- fix: improve page load performance for track overview
- chore: update dependencies

# 1.26.1 - (28.07.24)
- fix: annual statistics: round average number of tracks
- fix: line break long shared links on mobile devices
- fix: hide navbar toggler on mobile devices if not logged in
- fix: shared tracks/planned tours: set title and meta description

# 1.26.0 - (26.07.24)
- add: tracks and planned tours can now be shared via public links
- add: moved calendar chart from chart overview to navbar menu entry "analytics"
- fix: improve calendar responsiveness

# 1.25.0 - (17.07.24)
- add: maintenance events: show distance since last event with same description

# 1.24.0 - (23.06.24)
- add: map: add toggle button to switch between tracks and planned tours
- fix: errors during generation of preview image for a planned tour no longer prevents saving a planned tour
- chore: update dependencies

# 1.23.0 - (21.05.24)
- BREAKING CHANGE: you must update your settings.json (new section "gpxPreviewImages", see settings-example.json)
- add: planned tours: show preview images
- add: planned tours: open map on click on preview image
- chore: update dependencies

# 1.22.1 - (20.05.24)
- fix: calculation of annual statistics

# 1.22.0 - (19.05.24)
- add: added annual statistics page
- add: planned tours: open map in click on preview image
- fix: improve search page if there are no search result
- chore: update dependencies

# 1.21.0 - (07.05.24)
- add: planned tours now allow to specify their arrival and departure method (e.g. by car, by train, ...)
- add: planned tours now allow to specify their direction (e.g. single, roundtrip, ...)
- add: if a new planned tour is shared with you or an existing shared planned tour is modified, they will be marked with a notification
- fix: sort planned tours by name ascending
- chore: update dependencies

# 1.20.0 - (27.04.24)
- add: planned tours can be shared with other users

# 1.19.0 - (27.04.24)
- add: grouped navbar entries
- add: update icon for hiking
- add: easter eggs
- fix: only allow gpx files to be uploade for tracks and planned tours
- fix: responsiveness for maintenance events page
- fix: responsiveness for track form page
- fix: responsiveness for gpx form
- fix: truncate long usernames
- chore: update dependencies

# 1.18.0 - (22.04.24)
- add: maintenance events: show distance since event
- add: show icon for each navbar entry and headline
- add: split username and settings in navbar
- add: add icon for each input field
- add: add icon for each button
- fix: debug log messages for all CRUD methods
- chore: update dependencies

# 1.17.0 - (17.04.24)
- add: it is now possible to track maintenance events for each sport type
- add: extended dummy data generator
- fix: month names on search results page are now localized
- chore: update dependencies

# 1.16.1 - (01.04.24)
- fix: year/month select: improve usability on mobile devices
- fix: map: overflowing buttons
- fix: chart "duration per track" and chart "speed per track": some track names were not shown even if two tracks existed

# 1.16.0 - (26.03.24)
- add: year and month select on tracks page
- add: map: improve year filter options (do not reload page after single year is selected)
- chore: update dependencies

# 1.15.1 - (17.03.24)
- fix: track delete button does not work
- fix: month goal delete button does not work

# 1.15.0 - (16.03.24)
- add: add quick filter buttons for track types on track page
- add: add quick filter buttons for track types on month goal page
- add: add quick filter buttons for track types on search page
- add: add quick filter buttons for track types and years on map page
- add: new chart "speed per track"
- add: show confirmation dialogs on deletion of tracks, gpx files, month goals, custom fields and participants
- fix: broken search page and improve responsiveness
- fix: custom fields: show display name for type instead of enum name on settings page
- fix: month goal distance: inputs not prefilled if german is activated
- fix: gpx upload
- chore: update dependencies

# 1.14.0 - (09.03.24)
- add: track overview: toggle months by swiping left or right
- add: improve track overview (added icons, re-organize cards, improve text and icons on mobile devices)
- fix: track overview: map link is clickable again
- chore: update dependencies

# 1.13.0 - (28.02.24)
- add: it is now possible to specify participants for each track
- add: custom track fields: prevent usage of reserved or already used names
- add: improved responsiveness for different screen sizes
- add: track overview: only show current month and hide hotkey tip on small screens
- add: added tests
- chore: update dependencies

# 1.12.0 - (15.02.24)
- add: map: added button to collapse/expand legend
- fix: map: sort track legend by date
- fix: map: allow to fully zoom out
- chore: update dependencies

# 1.11.0 - (14.02.24)
- add: new track type "Hiking"
- add: show hint that arrow keys can be used to toggle between months
- BREAKING CHANGE: (automatic) database migration required for this release (see README.md)!
- chore: update dependencies

# 1.10.0 - (12.02.24)
- add: new chart: year calendar
- add: api: return id of created track or month goal
- add: new api route to upload a gpx track for an existing track
- add: new api route to fetch all existing tracks
- fix: set missing file extension for gpx download
- chore: update dependencies

# 1.9.2 - (09.02.24)
- fix: chart duration per track
- fix: achievement for month goal streak: fix calculation of streak
- ci: added code formatter and linter "ruff"
- ci: added type checker "mypy"

# 1.9.1 - (31.01.24)
- fix: wrong date localization at beginning of year
- fix: achievement for month goal streak: fix calculation of streak
- fix: achievement for month goal streak: current month should be added to streak if all goals are reached even if month is not over yet
- fix: edit track: distance input not prefilled
- fix: add missing grouping separator for large numbers
- chore: update dependencies

# 1.9.0 - (14.01.24)
- add: localize dates, numbers and maps
- chore: update dependencies

# 1.8.0 - (25.01.24)
- add: license, readme and screenshots
- add: dummy data generator
- add: improved chart and track chooser styling

# 1.7.2 - (11.01.24)
- fix: new track page not opening

# 1.7.1 - (07.01.24)
- fix: CORS errors

# 1.7.0 - (07.01.24)
- add: gpx files can be uploaded and attached to a track
- add: gpx files can be viewed on an interactive map
- add: show an elevation chart for gpx tracks on map
- add: show a speed chart for gpx tracks on map
- add: a single gpx track on map will be shown with "hotline" feature (green to red gradient along the track showing the speed)
- add: automatically join multiple track and segments in gpx files to allow them to be shown on map

# 1.6.1 - (28.12.23)
- fix: overlapping data points in chart for average speed
- fix: calculation of month goal streak achievement
- fix: ordering of changelog entries

# 1.6.0 - (23.12.23)
- add: search for tracks by name
- add: jump to month and year after editing/creating a track

# 1.5.1 - (11.12.23)
- fix: improved form input field size for durations
- fix: allow month goals to be created before 2023

# 1.5.0 - (28.11.23)
- add: values shown for each track in track list are now configurable in user settings
- fix: sort case-insensitive
- fix: prevent deletion of admin user

# 1.4.2 - (26.11.23)
- fix: custom field form

# 1.4.1 - (26.11.23)
- fix: track edit page

# 1.4.0 - (26.11.23)
- BREAKING CHANGE: replaced special track classes with single class and custom fields
- add: new chart: average speed (bar chart)
- add: new chart: distance per custom field (pie chart)
- add: new chart: duration per track name
- add: allow bulk creation of month goals
- add: autocomplete for already used track names in new track form
- add: new about page with changelog

# 1.3.0 - (21.11.23)
- fix charts: fill missing years and months
- fix: charts: fixed clipped legend
- fix: charts: cast number to int/float
- fix: deletion of month goals

# 1.2.0 - (19.11.23)
- add: localization for achievements
- add: new chart: distance per bike
- fix: improve date conversion

# 1.1.0 - (18.11.23)
- add: added achievements page
- fix: only show data for current user in charts

# 1.0.0 - (18.11.23)
- initial release
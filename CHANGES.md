# 1.28.0
- add: search: add pagination on bottom
- add: show edit button for track and planned tour map

# 1.27.0
- add: allow tracks to be linked to a planned tour
- fix: improve page load performance for track overview
- chore: update dependencies

# 1.26.1
- fix: annual statistics: round average number of tracks
- fix: line break long shared links on mobile devices
- fix: hide navbar toggler on mobile devices if not logged in
- fix: shared tracks/planned tours: set title and meta description

# 1.26.0
- add: tracks and planned tours can now be shared via public links
- add: moved calendar chart from chart overview to navbar menu entry "analytics"
- fix: improve calendar responsiveness

# 1.25.0
- add: maintenance events: show distance since last event with same description

# 1.24.0
- add: map: add toggle button to switch between tracks and planned tours
- fix: errors during generation of preview image for a planned tour no longer prevents saving a planned tour
- chore: update dependencies

# 1.23.0
- BREAKING CHANGE: you must update your settings.json (new section "gpxPreviewImages", see settings-example.json)
- add: planned tours: show preview images
- add: planned tours: open map on click on preview image
- chore: update dependencies

# 1.22.1
- fix: calculation of annual statistics

# 1.22.0
- add: added annual statistics page
- add: planned tours: open map in click on preview image
- fix: improve search page if there are no search result
- chore: update dependencies

# 1.21.0
- add: planned tours now allow to specify their arrival and departure method (e.g. by car, by train, ...)
- add: planned tours now allow to specify their direction (e.g. single, roundtrip, ...)
- add: if a new planned tour is shared with you or an existing shared planned tour is modified, they will be marked with a notification
- fix: sort planned tours by name ascending
- chore: update dependencies

# 1.20.0
- add: planned tours can be shared with other users

# 1.19.0
- add: grouped navbar entries
- add: update icon for hiking
- add: easter eggs
- fix: only allow gpx files to be uploade for tracks and planned tours
- fix: responsiveness for maintenance events page
- fix: responsiveness for track form page
- fix: responsiveness for gpx form
- fix: truncate long usernames
- chore: update dependencies

# 1.18.0
- add: maintenance events: show distance since event
- add: show icon for each navbar entry and headline
- add: split username and settings in navbar
- add: add icon for each input field
- add: add icon for each button
- fix: debug log messages for all CRUD methods
- chore: update dependencies

# 1.17.0
- add: it is now possible to track maintenance events for each sport type
- add: extended dummy data generator
- fix: month names on search results page are now localized
- chore: update dependencies

# 1.16.1
- fix: year/month select: improve usability on mobile devices
- fix: map: overflowing buttons
- fix: chart "duration per track" and chart "speed per track": some track names were not shown even if two tracks existed

# 1.16.0
- add: year and month select on tracks page
- add: map: improve year filter options (do not reload page after single year is selected)
- chore: update dependencies

# 1.15.1
- fix: track delete button does not work
- fix: month goal delete button does not work

# 1.15.0
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

# 1.14.0
- add: track overview: toggle months by swiping left or right
- add: improve track overview (added icons, re-organize cards, improve text and icons on mobile devices)
- fix: track overview: map link is clickable again
- chore: update dependencies

# 1.13.0
- add: it is now possible to specify participants for each track
- add: custom track fields: prevent usage of reserved or already used names
- add: improved responsiveness for different screen sizes
- add: track overview: only show current month and hide hotkey tip on small screens
- add: added tests
- chore: update dependencies

# 1.12.0
- add: map: added button to collapse/expand legend
- fix: map: sort track legend by date
- fix: map: allow to fully zoom out
- chore: update dependencies

# 1.11.0
- add: new track type "Hiking"
- add: show hint that arrow keys can be used to toggle between months
- BREAKING CHANGE: (automatic) database migration required for this release (see README.md)!
- chore: update dependencies

# 1.10.0
- add: new chart: year calendar
- add: api: return id of created track or month goal
- add: new api route to upload a gpx track for an existing track
- add: new api route to fetch all existing tracks
- fix: set missing file extension for gpx download
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
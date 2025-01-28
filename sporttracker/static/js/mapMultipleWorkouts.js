document.addEventListener('DOMContentLoaded', function()
{

    if(mapMode === 'workouts')
    {
        initMap(sortWorkoutsByName);
    }
    else
    {
        initMap(sortPlannedToursByName);
    }
});

function initMap(itemSortFunction)
{
    let map = initMapBase();

    if(gpxInfo.length === 0)
    {
        return;
    }

    let workouts = [];
    for(let i = 0; i < gpxInfo.length; i++)
    {
        const info = gpxInfo[i];
        workouts.push(info['gpxUrl'])
    }

    map.on('plugins_loaded', function(e)
    {
        L.GpxGroup.include({
            _onRouteMouseOver: function(route, polyline)
            {
            },
            _onRouteClick: function(route, polyline)
            {
                this.highlight(route, polyline);
                if(this.options.legend)
                {
                    this.setSelection(route);
                    L.DomUtil.get('legend_' + route._leaflet_id).parentNode.previousSibling.click();
                }
            },
            _loadGeoJSON: function(geojson, fallbackName)
            {
                if(geojson)
                {
                    const workoutId = fallbackName;
                    const gpxInfoForWorkout = getGpxInfoById(workoutId);

                    geojson.name = '<a href="' + gpxInfoForWorkout.workoutUrl + '">' + gpxInfoForWorkout.workoutName + '</a>'
                    this._loadRoute(geojson, gpxInfoForWorkout.gpxUrl);
                }
            },
            _loadRoute: function(data, gpxUrl)
            {
                if(!data)
                {
                    return;
                }

                var line_style = {
                    color: this._uniqueColors(this._tracks.length)[this._tracks.indexOf(gpxUrl)],  // access color by real index in workouts array instead of count of loaded elements
                    opacity: 0.75,
                    weight: 5,
                    distanceMarkers: this.options.distanceMarkers_options,
                };

                var route = L.geoJson(data, {
                    name: data.name || '',
                    style: (feature) => line_style,
                    distanceMarkers: line_style.distanceMarkers,
                    originalStyle: line_style,
                    filter: feature => feature.geometry.type != "Point",
                });

                this._elevation.import(this._elevation.__LGEOMUTIL).then(() =>
                {
                    route.addTo(this._layers);

                    route.eachLayer((layer) => this._onEachRouteLayer(route, layer));
                    this._onEachRouteLoaded(route);
                });
            },
        });

        function getGpxInfoById(workoutId)
        {
            return gpxInfo.find(info =>
            {
                return info.workoutId === parseInt(workoutId);
            });
        }

        let routes = L.gpxGroup(workouts, {
            points: [],
            point_options: {},
            elevation: true,
            elevation_options: initElevationChartSettings(false, 'disabled', 'inline'),
            legend: true,
            distanceMarkers: false
        });

        routes._legend.options.sortLayers = true
        routes._legend.options.sortFunction = itemSortFunction

        routes.addTo(map);

        let numberOfLoadedLayers = 0;
        let legendItemAlreadyClicked = false;
        map.on('layeradd', function(evt)
        {
            if(evt.layer._latlngs !== undefined)
            {
                numberOfLoadedLayers++;
            }

            if(numberOfLoadedLayers === workouts.length && !legendItemAlreadyClicked)
            {
                setTimeout(function()
                {
                    let firstLegendItem = document.querySelector('.leaflet-right .leaflet-control-layers-base label');
                    firstLegendItem.click();
                    legendItemAlreadyClicked = true;
                    map.fitBounds(routes.getBounds());
                }, 500);
            }
        });

        const stateChangingButton = L.easyButton({
            position: 'topright',
            states: [
                {
                    stateName: 'collapse-layers',
                    icon: '<i class="material-symbols-outlined">layers_clear</i>',
                    title: map_locale['button_collapse_layers'],
                    onClick: function(btn, map)
                    {
                        routes._legend.collapse();
                        btn.state('expand-layers');
                    }
                },
                {
                    stateName: 'expand-layers',
                    icon: '<i class="material-symbols-outlined">layers</i>',
                    title: map_locale['button_expand_layers'],
                    onClick: function(btn, map)
                    {
                        routes._legend.expand();
                        btn.state('collapse-layers');
                    }
                }]
        });
        stateChangingButton.addTo(map);
    });
}

const PATTERN_WORKOUT_NAME = /(\d{4}-\d{2}-\d{2} - .*)<\/a>/;
const PATTERN_PLANNED_TOUR_NAME = /<a.*>(.*)<\/a>/;

function sortWorkoutsByName(layerA, layerB, nameA, nameB)
{
    let realNameA = PATTERN_WORKOUT_NAME.exec(nameA)[1];
    let realNameB = PATTERN_WORKOUT_NAME.exec(nameB)[1];
    if(realNameA < realNameB)
    {
        return 1;
    }
    if(realNameA > realNameB)
    {
        return -1;
    }
    return 0;
}

function sortPlannedToursByName(layerA, layerB, nameA, nameB)
{
    let realNameA = PATTERN_PLANNED_TOUR_NAME.exec(nameA)[1].toLowerCase();
    let realNameB = PATTERN_PLANNED_TOUR_NAME.exec(nameB)[1].toLowerCase();
    if(realNameA > realNameB)
    {
        return 1;
    }
    if(realNameA < realNameB)
    {
        return -1;
    }
    return 0;
}
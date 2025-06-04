document.addEventListener('DOMContentLoaded', function()
{
    if(isTileHuntingOverlayEnabled)
    {
        const tileHuntingCheckboxes = document.getElementsByClassName('tileHuntingCheckbox');
        for(let i = 0; i < tileHuntingCheckboxes.length; i++)
        {
            tileHuntingCheckboxes[i].addEventListener('change', function()
            {
                window.location.href = tileHuntingCheckboxes[i].dataset.url;
            });
        }
    }

    if(mapMode === 'workouts')
    {
        initMap(sortWorkoutsByName, () => {});
    }
    else if(mapMode === 'plannedTours')
    {
        initMap(sortPlannedToursByName, () => {});
    }
    else if(mapMode === 'longDistanceTour')
    {
        initMap(sortLongDistanceTourStagesByOrder, onLongDistanceRouteSelected);
    }
});

function initMap(itemSortFunction, onRouteSelectedCallback)
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

    if(isTileHuntingOverlayEnabled)
    {
        const checkBoxEnableTileHunting = document.getElementById('tileHuntingEnableTiles');
        if(checkBoxEnableTileHunting !== null && checkBoxEnableTileHunting.checked)
        {
            L.tileLayer(tileRenderUrl + '/{z}/{x}/{y}.png', {
                minZoom: 9,
                maxZoom: 16
            }).addTo(map);
        }
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
            _onRouteSelected: function(route, polyline) {
                if(route.isSelected())
                {
                    onRouteSelectedCallback(route);
                }
                else
                {
                    this.unhighlight(route, polyline);
                }
            },
            _loadGeoJSON: function(geojson, fallbackName)
            {
                if(geojson)
                {
                    const workoutId = fallbackName;
                    const gpxInfoForWorkout = getGpxInfoById(workoutId);

                    geojson.name = '<a href="' + gpxInfoForWorkout.workoutUrl + '" target="_blank" class="map-layer-link" data-name="' + gpxInfoForWorkout.workoutName + '">' + gpxInfoForWorkout.workoutName + '</a>'
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
const PATTERN_LONG_DISTANCE_TOUR_STAGE_ORDER = /<a.*>\w+\s(\d+)\s-\s.*<\/a>/;


function sortByName(layerA, layerB, nameA, nameB, pattern, ignoreCase, ascending)
{
    let realNameA = pattern.exec(nameA)[1];
    let realNameB = pattern.exec(nameB)[1];

    if(ignoreCase === true)
    {
        realNameA = realNameA.toLowerCase();
        realNameB = realNameB.toLowerCase();
    }

    if(ascending)
    {
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

function sortByOrder(layerA, layerB, nameA, nameB, pattern)
{
    let realNameA = pattern.exec(nameA)[1];
    let realNameB = pattern.exec(nameB)[1];

    let realIntA = parseInt(realNameA);
    let realIntB = parseInt(realNameB);

    if(realIntA > realIntB)
    {
        return 1;
    }
    if(realIntA < realIntB)
    {
        return -1;
    }
    return 0;
}

function sortWorkoutsByName(layerA, layerB, nameA, nameB)
{
    return sortByName(layerA, layerB, nameA, nameB, PATTERN_WORKOUT_NAME, false, false);
}

function sortPlannedToursByName(layerA, layerB, nameA, nameB)
{
    return sortByName(layerA, layerB, nameA, nameB, PATTERN_PLANNED_TOUR_NAME, true, true);
}

function sortLongDistanceTourStagesByOrder(layerA, layerB, nameA, nameB)
{
    return sortByOrder(layerA, layerB, nameA, nameB, PATTERN_LONG_DISTANCE_TOUR_STAGE_ORDER);
}

function onLongDistanceRouteSelected(route)
{
    document.querySelectorAll('.stage').forEach((stage) =>
    {
        stage.classList.toggle('border', false);
        stage.classList.toggle('border-5', false);
        stage.classList.toggle('border-danger', false);
    })

    let stageId = PATTERN_LONG_DISTANCE_TOUR_STAGE_ORDER.exec(route.options.name)[1];
    let stageCard = document.getElementById('stage-' + stageId);
    stageCard.classList.add('border', 'border-5', 'border-danger');

    stageCard.scrollIntoView({behavior: "smooth"});
}
document.addEventListener('DOMContentLoaded', function()
{
    initMap();
});

const PATTERN_TRACK_NAME = /(\d{4}-\d{2}-\d{2} - .*)<\/a>/;

function initMap()
{
    let map = initMapBase();

    if(gpxInfo.length === 0)
    {
        return;
    }

    let tracks = [];
    for(let i = 0; i < gpxInfo.length; i++)
    {
        const info = gpxInfo[i];
        tracks.push(info['gpxUrl'])
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
                    const trackId = fallbackName;
                    const gpxInfoForTrack = getGpxInfoById(trackId);

                    geojson.name = '<a href="' + gpxInfoForTrack.trackUrl + '">' + gpxInfoForTrack.trackName + '</a>'
                    this._loadRoute(geojson, gpxInfoForTrack.gpxUrl);
                }
            },
            _loadRoute: function(data, gpxUrl)
            {
                if(!data)
                {
                    return;
                }

                var line_style = {
                    color: this._uniqueColors(this._tracks.length)[this._tracks.indexOf(gpxUrl)],  // access color by real index in tracks array instead of count of loaded elements
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

        function getGpxInfoById(trackId)
        {
            return gpxInfo.find(info =>
            {
                return info.trackId === parseInt(trackId);
            });
        }

        let routes = L.gpxGroup(tracks, {
            points: [],
            point_options: {},
            elevation: true,
            elevation_options: initElevationChartSettings(false, 'disabled'),
            legend: true,
            distanceMarkers: false
        });

        routes._legend.options.sortLayers = true
        routes._legend.options.sortFunction = function(layerA, layerB, nameA, nameB)
        {
            let realNameA = PATTERN_TRACK_NAME.exec(nameA)[1];
            let realNameB = PATTERN_TRACK_NAME.exec(nameB)[1];
            if(realNameA < realNameB)
            {
                return 1;
            }
            if(realNameA > realNameB)
            {
                return -1;
            }
            return 0;
        };

        routes.addTo(map);

        let numberOfLoadedLayers = 0;
        let legendItemAlreadyClicked = false;
        map.on('layeradd', function(evt)
        {
            if(evt.layer._latlngs !== undefined)
            {
                numberOfLoadedLayers++;
            }

            if(numberOfLoadedLayers === tracks.length && !legendItemAlreadyClicked)
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
                    icon: '<i class="material-icons">layers_clear</i>',
                    title: map_locale['button_collapse_layers'],
                    onClick: function(btn, map)
                    {
                        routes._legend.collapse();
                        btn.state('expand-layers');
                    }
                },
                {
                    stateName: 'expand-layers',
                    icon: '<i class="material-icons">layers</i>',
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
document.addEventListener('DOMContentLoaded', function()
{
    initMap();
});

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

                    geojson.name = '<a href="' + gpxInfoForTrack.trackUrl+ '">' + gpxInfoForTrack.trackName + '</a>'
                    this._loadRoute(geojson);
                }
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
            elevation_options: initElevationChartSettings(),
            legend: true,
            distanceMarkers: false
        });

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
    });
}
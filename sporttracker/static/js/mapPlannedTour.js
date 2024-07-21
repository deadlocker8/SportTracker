document.addEventListener('DOMContentLoaded', function()
{
    initMap();
});

function initMap()
{
    let map = initMapBase();

    if(gpxUrl === null)
    {
        return;
    }

    map.on('plugins_loaded', function(e)
    {
        let controlElevation = L.control.elevation(initElevationChartSettings(false, false, false)).addTo(map);
        controlElevation.load(gpxUrl);
    });
}
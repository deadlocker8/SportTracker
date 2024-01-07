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

    let controlElevation = L.control.elevation(initElevationChartSettings()).addTo(map);
    controlElevation.load(gpxInfo[0].gpxUrl);
}
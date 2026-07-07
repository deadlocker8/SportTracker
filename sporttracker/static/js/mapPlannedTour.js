document.addEventListener('DOMContentLoaded', function()
{
    const tileHuntingCheckboxes = document.getElementsByClassName('tileHuntingCheckbox');
    for(let i = 0; i < tileHuntingCheckboxes.length; i++)
    {
        tileHuntingCheckboxes[i].addEventListener('change', function()
        {
            window.location.href = tileHuntingCheckboxes[i].dataset.url;
        });
    }

    initMap();
});

function initMap()
{
    let map = initMapBase();

    if(gpxUrl === null)
    {
        return;
    }

    const checkBoxEnableTileHunting = document.getElementById('tileHuntingEnableTiles');
    if(checkBoxEnableTileHunting !== null && checkBoxEnableTileHunting.checked)
    {
        initTileHuntingVectorLayer(map, tileApiUrl, isGridActive);
    }

    map.on('plugins_loaded', function(e)
    {
        let controlElevation = L.control.elevation(initElevationChartSettings(false, false, false)).addTo(map);
        controlElevation.load(gpxUrl);
    });
}
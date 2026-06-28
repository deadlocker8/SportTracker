document.addEventListener('DOMContentLoaded', function()
{
    const checkboxGrid = document.getElementById('tileHuntingEnableGrid');
    checkboxGrid.addEventListener('change', function()
    {
        window.location.href = checkboxGrid.dataset.url;
    });

    initMap();
});

function initMap()
{
    let map = initMapBase();

    initTileHuntingVectorLayer(map, tileApiUrl);

    map.on('click', function(e)
    {
        const url = numberOfVisitsUrl + '/' + e.latlng.lat + '/' + e.latlng.lng;
        let xhr = new XMLHttpRequest();
        xhr.open('GET', url);
        xhr.onload = function()
        {
            if(xhr.status === 200)
            {
                let response = JSON.parse(xhr.response);
                L.popup().setLatLng(e.latlng).setContent(response.numberOfVisits.toString() + ' ' + numberOfVisitsText).openOn(map);
            }
        };
        xhr.send();
    });
}

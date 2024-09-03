document.addEventListener('DOMContentLoaded', function()
{
    initMap();
});

function initMap()
{
    let map = initMapBase();

    L.tileLayer(tileRenderUrl + '/{z}/{x}/{y}.png', {
        minZoom: 9,
        maxZoom: 16
    }).addTo(map);
}

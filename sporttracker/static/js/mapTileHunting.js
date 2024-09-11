document.addEventListener('DOMContentLoaded', function()
{
    const buttonHelp = document.getElementById('button-help');
    new bootstrap.Tooltip(buttonHelp, {});

    initMap();
});

function initMap()
{
    let map = initMapBase();

    L.tileLayer(tileRenderUrl + '/{z}/{x}/{y}.png', {
        minZoom: 9,
        maxZoom: 16
    }).addTo(map);

    map.on('zoomend', function(e)
    {
        const currentZoom = map.getZoom();
        document.getElementById('warning-zoom').classList.toggle('d-none', currentZoom >= 9);
    });
}

document.addEventListener('DOMContentLoaded', function()
{
    const buttonHelp = document.getElementById('button-help');
    new bootstrap.Tooltip(buttonHelp, {});

    const buttonHelpMaxSquare = document.getElementById('button-help-max-square');
    new bootstrap.Tooltip(buttonHelpMaxSquare, {sanitize: false});

    const checkboxGrid = document.getElementById('tileHuntingEnableGrid');
    checkboxGrid.addEventListener('change', function()
    {
        window.location.href = checkboxGrid.dataset.url;
    });
    const checkboxMaxSquare = document.getElementById('tileHuntingEnableMaxSquare');
    checkboxMaxSquare.addEventListener('change', function()
    {
        window.location.href = checkboxMaxSquare.dataset.url;
    });

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

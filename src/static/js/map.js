document.addEventListener('DOMContentLoaded', function()
{
    initMap(false);
});

function initMap(enableTiles)
{
    const markerIcon = new L.Icon.Default;

    let map = L.map('map', {
        attributionControl: false,
        zoomControl: false,
        minZoom: 6,
        maxZoom: 16,
    }).setView([51, 13], 6);

    L.control.zoom({position: 'topright'}).addTo(map);
    L.control.scale({position: 'bottomright'}).addTo(map);
    let attributionControl = L.control.attribution({position: 'bottomleft'}).addTo(map);
    attributionControl.setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');

    if(enableTiles)
    {
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 16,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
    }

    function createLayer(gpxUrl)
    {
        return new L.GPX(gpxUrl, {
            async: true,
            marker_options: {
                startIcon: markerIcon,
                endIcon: markerIcon,
                wptIcons: {'': markerIcon},
            },
        });
    }

    if(gpxInfo.length === 0)
    {
        return;
    }

    let layers = [];
    let overlays = {};
    for(let i = 0; i < gpxInfo.length; i++)
    {
        const info = gpxInfo[i];
        const layer = createLayer(info['gpxUrl'])
        layers.push(layer);
        overlays['<a href="' + info['trackUrl'] + '">' + info['trackName'] + '</a>'] = layer;
    }

    let tracksLayer = L.featureGroup(layers);
    tracksLayer.addTo(map);
    layers[layers.length - 1].on('loaded', function()
    {
        map.fitBounds(tracksLayer.getBounds());

        L.control.layers(null, overlays, {collapsed: false}).addTo(map);

        map.on('overlayadd', function(event)
        {
            map.fitBounds(event.layer.getBounds());
        });
    });
}
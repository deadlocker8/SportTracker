function initElevationChartSettings()
{
    return {
        theme: 'custom-theme',
        detached: true,
        autofitBounds: true,
        summary: 'summary',
        imperial: false,
        closeBtn: false,
        altitude: true,
        slope: false,
        speed: 'disabled',
        acceleration: false,
        time: 'summary',
        legend: true,
        followMarker: false,
        almostOver: true,
        distanceMarkers: false,
        hotline: 'speed',
        distance: true,
        edgeScale: false,
        height: document.documentElement.clientHeight * 0.22,
        downloadLink: false
    }
}

function initMapBase()
{
    L.registerLocale('map_locale', map_locale);
    L.setLocale('map_locale');

    let map = L.map('map', {
        attributionControl: false,
        minZoom: 0,
        maxZoom: 16,
        mapTypeId: 'streets',
        mapTypeIds: ['streets', 'satellite'],
        gestureHandling: false,
        pegmanControl: false,
        locateControl: false,
        fullscreenControl: true,
        layersControl: true,
        minimapControl: false,
        editInOSMControl: false,
        loadingControl: false,
        rotateControl: false,
        searchControl: true,
        disableDefaultUI: false,
        zoomControl: {
            position: 'topright'
        },
        plugins: [
            'd3@7.8.4/dist/d3.min.js',
            '@tmcw/togeojson@5.6.2/dist/togeojson.umd.js',
            'leaflet-geometryutil@0.9.3/src/leaflet.geometryutil.js',
            'leaflet-almostover@1.0.1/src/leaflet.almostover.js',
            '@raruto/leaflet-elevation@2.5.1/dist/leaflet-elevation.min.css',
            '@raruto/leaflet-elevation@2.5.1/dist/leaflet-elevation.min.js',
            '@raruto/leaflet-elevation@2.5.1/libs/leaflet-gpxgroup.js',
        ]
    }).setView([51, 13], 6);

    let attributionControl = L.control.attribution({position: 'bottomleft'}).addTo(map);
    attributionControl.setPrefix('<a href="https://leafletjs.com/" > Leaflet </a>');

    return map;
}
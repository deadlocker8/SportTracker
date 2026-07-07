function initElevationChartSettings(hotlineMode, speedMode, summaryMode)
{
    return {
        theme: 'custom-theme',
        detached: true,
        autofitBounds: true,
        summary: summaryMode,
        imperial: false,
        closeBtn: false,
        altitude: true,
        slope: false,
        speed: speedMode,
        acceleration: false,
        time: 'summary',
        legend: true,
        followMarker: false,
        almostOver: true,
        distanceMarkers: false,
        hotline: hotlineMode,
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

function createGridLayer()
{
    const tileGridLayer = L.Layer.extend({
        onAdd(map)
        {
            this._map = map;

            this._canvas = L.DomUtil.create("canvas", "tile-grid-canvas");
            this._ctx = this._canvas.getContext("2d");

            map.getPanes().tooltipPane.appendChild(this._canvas);

            map.on("move zoom resize", this._draw, this);

            this._resize();
            this._draw();
        },

        onRemove(map)
        {
            map.off("move zoom resize", this._draw, this);
            this._canvas.remove();
        },

        _resize()
        {
            const size = this._map.getSize();

            this._canvas.width = size.x;
            this._canvas.height = size.y;

            L.DomUtil.setPosition(
                this._canvas,
                this._map.containerPointToLayerPoint([0, 0])
            );
        },

        _draw()
        {
            const map = this._map;
            const ctx = this._ctx;

            this._resize();

            if(map.getZoom() < mapMinZoomLevel)
            {
                ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
                return;
            }

            ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);

            const bounds = map.getBounds();

            const nw = map.project(bounds.getNorthWest(), baseZoomLevel).divideBy(256).floor();
            const se = map.project(bounds.getSouthEast(), baseZoomLevel).divideBy(256).floor();

            ctx.beginPath();
            ctx.strokeStyle = "#000000C8";
            ctx.lineWidth = 1;

            for(let x = nw.x; x <= se.x; x++)
            {
                for(let y = nw.y; y <= se.y; y++)
                {
                    const topLeft = map.unproject(L.point(x * 256, y * 256), baseZoomLevel);
                    const bottomRight = map.unproject(L.point((x + 1) * 256, (y + 1) * 256), baseZoomLevel);

                    const p1 = map.latLngToContainerPoint(topLeft);
                    const p2 = map.latLngToContainerPoint(bottomRight);

                    ctx.rect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);
                }
            }

            ctx.stroke();
        }
    });

    return new tileGridLayer();
}

function initTileHuntingVectorLayer(map, apiUrl)
{
    let tileLayer = L.geoJSON(null, {
        style: function(feature)
        {
            let style = {
                fillColor: feature.properties.fillColor,
                fillOpacity: feature.properties.fillOpacity,
                weight: feature.properties.weight || 0,
            };
            if(feature.properties.color)
            {
                style.color = feature.properties.color;
            }
            return style;
        }
    });

    let loadedTiles = new Set();
    let loadTimer = null;

    function doLoad()
    {
        __loadTileHuntingTiles(map, apiUrl, tileLayer, loadedTiles);
    }

    map.on('moveend', function()
    {
        loadTimer = __debouncedLoadTiles(loadTimer, doLoad);
    });

    map.on('zoomend', function(e)
    {
        const currentZoom = map.getZoom();
        const warningZoom = document.getElementById('warning-zoom');
        if(warningZoom)
        {
            warningZoom.classList.toggle('d-none', currentZoom >= mapMinZoomLevel);
        }

        if(currentZoom >= mapMinZoomLevel)
        {
            if(!map.hasLayer(tileLayer))
            {
                tileLayer.addTo(map);
            }
            loadTimer = __debouncedLoadTiles(loadTimer, doLoad);
        }
        else
        {
            if(map.hasLayer(tileLayer))
            {
                map.removeLayer(tileLayer);
            }
        }
    });

    doLoad();

    map.addLayer(createGridLayer());
}

function __loadTileHuntingTiles(map, apiUrl, tileLayer, loadedTiles)
{
    if(map.getZoom() < mapMinZoomLevel)
    {
        return;
    }

    const bounds = map.getBounds();
    const bbox = bounds.getWest() + ',' + bounds.getSouth() + ',' + bounds.getEast() + ',' + bounds.getNorth();
    const separator = apiUrl.indexOf('?') >= 0 ? '&' : '?';

    fetch(apiUrl + separator + 'bbox=' + encodeURIComponent(bbox)).then(function(response)
    {
        if(!response.ok)
        {
            throw new Error('Tile fetch failed');
        }
        return response.json();
    }).then(function(data)
    {
        let newFeatures = [];
        for(const element of data.features)
        {
            let key = element.properties.x + ',' + element.properties.y;
            if(!loadedTiles.has(key))
            {
                newFeatures.push(element);
                loadedTiles.add(key);
            }
        }
        if(newFeatures.length > 0)
        {
            tileLayer.addData({type: 'FeatureCollection', features: newFeatures});
        }
    }).catch(function(err)
    {
        console.error('Failed to load tiles:', err);
    });
}

function __debouncedLoadTiles(loadTimer, loadFn)
{
    if(loadTimer)
    {
        clearTimeout(loadTimer);
    }
    return setTimeout(loadFn, 200);
}
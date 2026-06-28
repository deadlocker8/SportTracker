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
    }).addTo(map);

    let loadedTiles = new Set();
    let loadTimer = null;

    function loadTiles()
    {
        const bounds = map.getBounds();
        const bbox = bounds.getWest() + ',' + bounds.getSouth() + ',' + bounds.getEast() + ',' + bounds.getNorth();

        fetch(tileApiUrl + '?bbox=' + encodeURIComponent(bbox))
            .then(function(response)
            {
                if(!response.ok)
                {
                    throw new Error('Tile fetch failed');
                }
                return response.json();
            })
            .then(function(data)
            {
                let newFeatures = [];
                for(let i = 0; i < data.features.length; i++)
                {
                    let key = data.features[i].properties.x + ',' + data.features[i].properties.y;
                    if(!loadedTiles.has(key))
                    {
                        newFeatures.push(data.features[i]);
                        loadedTiles.add(key);
                    }
                }
                if(newFeatures.length > 0)
                {
                    tileLayer.addData({type: 'FeatureCollection', features: newFeatures});
                }
            })
            .catch(function(err)
            {
                console.error('Failed to load tiles:', err);
            });
    }

    function debouncedLoadTiles()
    {
        if(loadTimer)
        {
            clearTimeout(loadTimer);
        }
        loadTimer = setTimeout(loadTiles, 200);
    }

    map.on('moveend', debouncedLoadTiles);

    map.on('zoomend', function(e)
    {
        const currentZoom = map.getZoom();
        document.getElementById('warning-zoom').classList.toggle('d-none', currentZoom >= mapMinZoomLevel);
    });

    loadTiles();
}

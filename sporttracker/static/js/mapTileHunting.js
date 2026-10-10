document.addEventListener('DOMContentLoaded', function()
{
    initTooltips('.button-help-tiles', {});
    initTooltips('.button-help-max-square', {sanitize: false});
    initTooltips('.button-help-max-cluster', {sanitize: false});

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

function initTooltips(selector, options)
{
    document.querySelectorAll(selector).forEach(function(element)
    {
        new bootstrap.Tooltip(element, options);
    });
}

function initMap()
{
    let map = initMapBase();
    initTileHuntingVectorLayer(map, tileApiUrl, isGridActive);
}

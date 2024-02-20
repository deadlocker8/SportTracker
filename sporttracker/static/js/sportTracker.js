document.addEventListener('DOMContentLoaded', function()
{
    let buttonGpxTrackDelete = document.getElementById('buttonGpxTrackDelete');
    if(buttonGpxTrackDelete !== null)
    {
        buttonGpxTrackDelete.addEventListener('click', function()
        {
            const url = buttonGpxTrackDelete.dataset.url;
            let xhr = new XMLHttpRequest();
            xhr.open('GET', url);
            xhr.onload = function()
            {
                if(xhr.status === 204)
                {
                    document.getElementById('gpxControlsEnabled').classList.toggle('hidden', true);
                    document.getElementById('gpxControlsDisabled').classList.toggle('hidden', false);
                }
            };
            xhr.send();
        });
    }
});
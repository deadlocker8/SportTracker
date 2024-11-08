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

    let buttonSharedLinkDelete = document.getElementById('buttonSharedLinkDelete');
    if(buttonSharedLinkDelete !== null)
    {
        buttonSharedLinkDelete.addEventListener('click', function()
        {
            document.getElementsByName('shareCode')[0].value = '';
            document.getElementById('sharedLinkControlsEnabled').classList.toggle('hidden', true);
            document.getElementById('buttonCreateSharedLink').classList.toggle('hidden', false);
        });
    }

    let buttonCopySharedLink = document.getElementById('buttonCopySharedLink');
    if(buttonCopySharedLink !== null)
    {
        buttonCopySharedLink.addEventListener('click', function()
        {
            navigator.clipboard.writeText(document.getElementById('sharedLink').innerText);
            const tooltip = new bootstrap.Tooltip(buttonCopySharedLink, {
                'trigger': 'manual'
            });
            tooltip.show();
            setTimeout(function()
            {
                tooltip.hide();
            }, 1000);
        });
    }

    let buttonCreateSharedLink = document.getElementById('buttonCreateSharedLink');
    if(buttonCreateSharedLink !== null)
    {
        buttonCreateSharedLink.addEventListener('click', function()
        {
            const url = buttonCreateSharedLink.dataset.url;
            let xhr = new XMLHttpRequest();
            xhr.open('GET', url);
            xhr.onload = function()
            {
                if(xhr.status === 200)
                {
                    let response = JSON.parse(xhr.response);

                    document.getElementsByName('shareCode')[0].value = response.shareCode;
                    document.getElementById('sharedLink').href = response.url;
                    document.getElementById('sharedLink').innerText = response.url;
                    document.getElementById('sharedLinkControlsEnabled').classList.toggle('hidden', false);
                    document.getElementById('buttonCreateSharedLink').classList.toggle('hidden', true);
                }
            };
            xhr.send();
        });
    }
});
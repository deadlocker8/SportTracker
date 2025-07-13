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
            document.getElementsByName('share_code')[0].value = '';
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

                    document.getElementsByName('share_code')[0].value = response.shareCode;
                    document.getElementById('sharedLink').href = response.url;
                    document.getElementById('sharedLink').innerText = response.url;
                    document.getElementById('sharedLinkControlsEnabled').classList.toggle('hidden', false);
                    document.getElementById('buttonCreateSharedLink').classList.toggle('hidden', true);
                }
            };
            xhr.send();
        });
    }

    let checkboxMaintenanceReminder = document.getElementById('maintenance-event-reminder-checkbox');
    if(checkboxMaintenanceReminder !== null)
    {
        checkboxMaintenanceReminder.addEventListener('click', function()
        {
            document.getElementById('maintenance-event-reminder').classList.toggle('hidden', !checkboxMaintenanceReminder.checked);
        });
    }

    let maintenanceEventTypeSelect = document.getElementById('maintenance-event-type');
    if(maintenanceEventTypeSelect !== null)
    {
        maintenanceEventTypeSelect.addEventListener('change', function()
        {
            let selectedValue = maintenanceEventTypeSelect.value;
            document.getElementById('maintenance-event-reminder-container').classList.toggle('hidden', selectedValue === 'FITNESS');
        });

        let selectedValue = maintenanceEventTypeSelect.value;
        document.getElementById('maintenance-event-reminder-container').classList.toggle('hidden', selectedValue === 'FITNESS');
    }

    let buttonImportFromFitFile = document.getElementById('buttonImportFromFitFile');
    if(buttonImportFromFitFile !== null)
    {
        buttonImportFromFitFile.addEventListener('click', function()
        {
            let form = document.getElementById('formImportFromFitFile');
            let warningMessageContainer = document.getElementById('warningMessageContainerImportFromFitFile');
            let formData = new FormData(form);
            toggleFitFileImport(buttonImportFromFitFile, true);

            let xhr = new XMLHttpRequest();
            xhr.open('POST', form.action);
            xhr.onload = function()
            {
                toggleFitFileImport(buttonImportFromFitFile, false);

                if(xhr.status === 200)
                {
                    window.location.href = buttonImportFromFitFile.dataset.url;
                }
                else
                {
                    warningMessageContainer.classList.toggle('hidden', false);
                    warningMessageContainer.querySelector('#warning-message').innerText = xhr.response;
                }
            };
            xhr.send(formData);
        });
    }

    let checkboxMaintenanceReminderNotifications = document.getElementById('isMaintenanceRemindersNotificationsActivated');
    if(checkboxMaintenanceReminderNotifications !== null)
    {
        checkboxMaintenanceReminderNotifications.addEventListener('click', function()
        {
            document.getElementById('ntfy-settings').classList.toggle('hidden', !checkboxMaintenanceReminderNotifications.checked);
        });
    }

    let buttonNtfyTest = document.getElementById('btn-ntfy-test');
    if(buttonNtfyTest !== null)
    {
        buttonNtfyTest.addEventListener('click', function()
        {
            let testUrl = buttonNtfyTest.dataset.url;
            let form = document.getElementById('ntfy-form');
            let warningMessageContainer = document.getElementById('warningMessageNtfy');
            let formData = new FormData(form);
            buttonNtfyTest.disabled = true;

            let xhr = new XMLHttpRequest();
            xhr.open('POST', testUrl);
            xhr.onload = function()
            {
                buttonNtfyTest.disabled = false;

                if(xhr.status === 200)
                {
                    warningMessageContainer.classList.toggle('hidden', false);
                    warningMessageContainer.classList.toggle('alert-danger', false);
                    warningMessageContainer.classList.toggle('alert-success', true);
                    warningMessageContainer.innerText = JSON.parse(xhr.response)['message'];
                }
                else
                {
                    warningMessageContainer.classList.toggle('hidden', false);
                    warningMessageContainer.classList.toggle('alert-danger', true);
                    warningMessageContainer.classList.toggle('alert-success', false);
                    warningMessageContainer.innerText = JSON.parse(xhr.response)['message'];
                }
            };
            xhr.send(formData);
        });
    }

    let isTileHuntingAccessActivated = document.getElementById('isTileHuntingAccessActivated');
    if(isTileHuntingAccessActivated !== null)
    {
        isTileHuntingAccessActivated.addEventListener('click', function()
        {
            document.getElementById('isTileHuntingShowPlannedTilesActivated').disabled = !isTileHuntingAccessActivated.checked;
        });
    }
});

function toggleFitFileImport(buttonImportFromFitFile, disable)
{
    let buttonCancelImportFromFitFile = document.getElementById('buttonCancelImportFromFitFile');
    let fileInput = document.getElementById('formFile');
    let spinner = buttonImportFromFitFile.querySelector('.spinner-border');

    spinner.classList.toggle('hidden', !disable);
    buttonCancelImportFromFitFile.disabled = disable;
    buttonImportFromFitFile.disabled = disable;
    fileInput.disabled = disable;
}
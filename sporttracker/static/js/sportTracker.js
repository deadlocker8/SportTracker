document.addEventListener('DOMContentLoaded', function()
{
    let buttonGpxTrackDelete = document.getElementById('buttonGpxTrackDelete');
    if(buttonGpxTrackDelete !== null)
    {
        buttonGpxTrackDelete.addEventListener('click', function()
        {
            automaticallyToggleSubmitButtons(buttonGpxTrackDelete, true);

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

                automaticallyToggleSubmitButtons(buttonGpxTrackDelete, false);
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

    let checkboxNtfySettingsIsActive = document.getElementById('ntfySettingsIsActive');
    if(checkboxNtfySettingsIsActive !== null)
    {
        checkboxNtfySettingsIsActive.addEventListener('click', function()
        {
            document.getElementById('ntfy-settings').classList.toggle('hidden', !checkboxNtfySettingsIsActive.checked);
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

    let buttonNtfySettingsSave = document.getElementById('button-ntfy-settings-save');
    if(buttonNtfySettingsSave !== null)
    {
        buttonNtfySettingsSave.addEventListener('click', function()
        {
            let form = document.getElementById('ntfy-form');
            let warningMessageContainer = document.getElementById('warningMessageNtfy');
            let formData = new FormData(form);

            let xhr = new XMLHttpRequest();
            xhr.open('POST', form.action);
            xhr.onload = function()
            {
                let ntfyErrorMessage = JSON.parse(xhr.response)['ntfyErrorMessage'];

                if(xhr.status !== 200 || ntfyErrorMessage !== null)
                {
                    warningMessageContainer.classList.toggle('hidden', false);
                    warningMessageContainer.classList.toggle('alert-danger', true);
                    warningMessageContainer.classList.toggle('alert-success', false);
                    warningMessageContainer.innerText = ntfyErrorMessage;
                }
                else
                {
                    window.location.href = buttonNtfySettingsSave.dataset.url;
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

    let buttonsDeleteModalAction = document.querySelectorAll('.button-delete-modal-action');
    for(let i = 0; i < buttonsDeleteModalAction.length; i++)
    {
        buttonsDeleteModalAction[i].addEventListener('click', function()
        {
            automaticallyToggleSubmitButtons(buttonsDeleteModalAction[i], true);
            window.location.href = buttonsDeleteModalAction[i].dataset.url;
        });
    }

    let badgesDebug = document.querySelectorAll('.badge-debug');
    for(let i = 0; i < badgesDebug.length; i++)
    {
        badgesDebug[i].addEventListener('click', function()
        {
            badgesDebug[i].style.display = 'none';
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

function automaticallyDisableButtonsOnFormSubmit(form)
{
    let buttonsSubmitAutomaticallyDisabled = form.getElementsByClassName('button-submit-automatically-disabled');
    for(let i = 0; i < buttonsSubmitAutomaticallyDisabled.length; i++)
    {
        automaticallyToggleSubmitButtons(buttonsSubmitAutomaticallyDisabled[i], true);
    }
    return true;
}

function automaticallyToggleSubmitButtons(buttonSubmitAutomaticallyDisabled, showProgressSpinner)
{
    buttonSubmitAutomaticallyDisabled.disabled = showProgressSpinner;

    // hide icon and text
    let icon = buttonSubmitAutomaticallyDisabled.querySelector('.material-symbols-outlined');
    if(icon !== null)
    {
        icon.classList.toggle('hidden', showProgressSpinner);
    }
    buttonSubmitAutomaticallyDisabled.querySelector('.button-automatically-disabled-text').classList.toggle('hidden', showProgressSpinner);

    // show spinner and disabled text
    buttonSubmitAutomaticallyDisabled.querySelector('.spinner-border').classList.toggle('hidden', !showProgressSpinner);
    buttonSubmitAutomaticallyDisabled.querySelector('.button-automatically-disabled-text-disabled').classList.toggle('hidden', !showProgressSpinner);

    // disable other buttons that could interfere with the form submit
    let buttonsToDisable = document.querySelectorAll('.button-automatically-disabled');
    buttonsToDisable.forEach((button) => button.disabled = showProgressSpinner);
}
const linkedPlannedToursList = document.getElementById('long-distance-tour-planned-tours');
const infoDragAndDrop = document.getElementById('info-drag-and-drop');
const infoNoLinkedTours = document.getElementById('info-no-linked-tours');
const infoNoPlannedTours = document.getElementById('info-no-planned-tours');
const workoutTypeSelect = document.getElementById('long-distance-tour-type');
const plannedTourSearchInput = document.getElementById('long-distance-tour-planned-tour-search');

init();


function init()
{
    new Sortable(linkedPlannedToursList, {
        ghostClass: 'active',
        revertOnSpill: true,
    });

    let deleteButtons = document.querySelectorAll('.button-long-distance-tour-unlink-planned-tour');
    for(let i = 0; i < deleteButtons.length; i++)
    {
        deleteButtons[i].addEventListener('click', () =>
        {
            onDeleteStage(deleteButtons[i]);
        });
    }

    let addButtons = document.querySelectorAll('.button-long-distance-tour-add-planned-tour');
    for(let i = 0; i < addButtons.length; i++)
    {
        addButtons[i].addEventListener('click', () =>
        {
            onAddStage(addButtons[i]);
        });
    }

    workoutTypeSelect.addEventListener('change', function(e) {
        clearStages();
        updateStagesAndAvailablePlannedTours();
    });

    plannedTourSearchInput.addEventListener('input', function(e) {
       updateStagesAndAvailablePlannedTours();
    });

    updateStagesAndAvailablePlannedTours();
}

function updateStagesAndAvailablePlannedTours()
{
    filterAvailablePlannedTours(workoutTypeSelect.value, plannedTourSearchInput.value.trim().toLowerCase());
    updateStageOrders();
    updateInfoMessages();
}

function updateStageOrders()
{
    let numberOfItems = document.querySelectorAll('.button-long-distance-tour-unlink-planned-tour').length;

    let ordersList = document.getElementById('long-distance-tour-orders');
    ordersList.innerHTML = '';

    for(let i = 0; i < numberOfItems; i++)
    {
        let newItem = document.createElement('li');
        newItem.classList.add('list-group-item', 'fw-bold');
        newItem.innerText = localeStage + ' ' + (i + 1);

        ordersList.appendChild(newItem);
    }
}

function onDeleteStage(button)
{
    let order = button.dataset.order;
    linkedPlannedToursList.removeChild(document.getElementById('long-distance-tour-linked-planned-tour-' + order));

    updateStagesAndAvailablePlannedTours();
}

function onAddStage(button)
{
    let id = button.dataset.id;

    let numberOfStages = linkedPlannedToursList.querySelectorAll('li').length;

    let newItem = document.createElement('li');
    newItem.classList.add('list-group-item', 'd-flex', 'align-items-center');
    newItem.id = 'long-distance-tour-linked-planned-tour-' + numberOfStages;

    let newName = document.createElement('span');
    newName.classList.add('flex-grow-1');
    newName.innerText = button.dataset.nameBeautified;
    newItem.appendChild(newName);

    let newDeleteButton = document.createElement('i');
    newDeleteButton.classList.add('material-symbols-outlined', 'fs-5', 'button-long-distance-tour-unlink-planned-tour');
    newDeleteButton.innerText = 'delete';
    newDeleteButton.dataset.order = numberOfStages.toString();
    newDeleteButton.dataset.id = id;
    newDeleteButton.addEventListener('click', () =>
    {
        onDeleteStage(newDeleteButton);
    });
    newItem.appendChild(newDeleteButton);

    let newHiddenInput = document.createElement('input');
    newHiddenInput.setAttribute('type', 'hidden');
    newHiddenInput.setAttribute('name', 'linkedPlannedTours');
    newHiddenInput.setAttribute('value', id);
    newItem.appendChild(newHiddenInput);

    linkedPlannedToursList.appendChild(newItem);

    updateStagesAndAvailablePlannedTours();
}

function updateInfoMessages()
{
    let hasLinkedPlannedTours = document.querySelectorAll('.button-long-distance-tour-unlink-planned-tour').length;

    infoDragAndDrop.classList.toggle('hidden', hasLinkedPlannedTours === 0);
    infoNoLinkedTours.classList.toggle('hidden', hasLinkedPlannedTours !== 0);

    infoNoPlannedTours.classList.toggle('hidden', document.querySelectorAll('.button-long-distance-tour-add-planned-tour:not(.hidden)').length > 0);
}

function filterAvailablePlannedTours(workoutType, searchText)
{
    // re-enable all available planned tours
    document.querySelectorAll('.button-long-distance-tour-add-planned-tour').forEach(e => {
        e.classList.toggle('hidden', false);
    });

    // hide planned tours that do not match the selected workout type
    document.querySelectorAll('.button-long-distance-tour-add-planned-tour:not([data-type="' + workoutType + '"])').forEach(e => {
        e.classList.toggle('hidden', true);
    });

    // hide planned tours that are already added as stages
    let alreadyUsedTours = document.querySelectorAll('.button-long-distance-tour-unlink-planned-tour');
    alreadyUsedTours.forEach(e => {
        document.querySelector('.button-long-distance-tour-add-planned-tour[data-id="' + e.dataset.id + '"]').classList.toggle('hidden', true);
    });

    // hide planned tours that do not contain the search text
    if(searchText.length > 0)
    {
        document.querySelectorAll('.button-long-distance-tour-add-planned-tour:not([data-name*="' + searchText + '"])').forEach(e => {
            e.classList.toggle('hidden', true);
        });
    }
}

function clearStages()
{
    let deleteButtons = document.querySelectorAll('.button-long-distance-tour-unlink-planned-tour');
    for(let i = 0; i < deleteButtons.length; i++)
    {
        deleteButtons[i].click();
    }
}
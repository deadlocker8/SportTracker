const linkedPlannedToursList = document.getElementById('long-distance-tour-planned-tours');
const availablePlannedToursList = document.getElementById('long-distance-tour-available-planned-tours');

new Sortable(linkedPlannedToursList, {
    ghostClass: 'active',
    revertOnSpill: true,
});

// delete item in list
let deleteButtons = document.querySelectorAll('.button-long-distance-tour-unlink-planned-tour');
for(let i = 0; i < deleteButtons.length; i++)
{
    deleteButtons[i].addEventListener('click', () =>
    {
        onDeleteStage(deleteButtons[i]);
    });
}

// add item to list
let addButtons = document.querySelectorAll('.button-long-distance-tour-add-planned-tour');
for(let i = 0; i < addButtons.length; i++)
{
    addButtons[i].addEventListener('click', () =>
    {
        let id = addButtons[i].dataset.id;

        let numberOfStages = linkedPlannedToursList.querySelectorAll('li').length;

        let newItem = document.createElement('li');
        newItem.classList.add('list-group-item', 'd-flex', 'align-items-center');
        newItem.id = 'long-distance-tour-linked-planned-tour-' + numberOfStages;

        let newName = document.createElement('span');
        newName.classList.add('flex-grow-1');
        newName.innerText = addButtons[i].innerText;
        newItem.appendChild(newName);

        let newDeleteButton = document.createElement('i');
        newDeleteButton.classList.add('material-symbols-outlined', 'fs-5', 'button-long-distance-tour-unlink-planned-tour');
        newDeleteButton.innerText = 'delete';
        newDeleteButton.dataset.order=numberOfStages.toString();
        newDeleteButton.dataset.id=id;
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

        addButtons[i].classList.toggle('hidden', true);
        updateStageOrders();


    });
}

updateStageOrders();

function updateStageOrders()
{
    let numberOfItems = document.querySelectorAll('.button-long-distance-tour-unlink-planned-tour')

    let ordersList = document.getElementById('long-distance-tour-orders');
    ordersList.innerHTML = '';

    for(let i = 0; i < numberOfItems.length; i++)
    {
        let newItem = document.createElement('li');
        newItem.classList.add('list-group-item', 'fw-bold');
        newItem.innerText = localeStage + ' ' + (i + 1);

        ordersList.appendChild(newItem);
    }
}

function onDeleteStage(item)
{
    let order = item.dataset.order;
    linkedPlannedToursList.removeChild(document.getElementById('long-distance-tour-linked-planned-tour-' + order));
    updateStageOrders();

    document.querySelector('.button-long-distance-tour-add-planned-tour[data-id="' + item.dataset.id + '"]').classList.toggle('hidden', false);
}
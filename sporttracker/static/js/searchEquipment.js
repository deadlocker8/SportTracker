document.addEventListener('DOMContentLoaded', function()
{
    const checkboxAllEquipment = document.getElementById('searchFilterAllEquipment');
    const buttonSelectEquipment = document.getElementById('buttonSearchEquipmentSelect');
    const selectedCountContainer = document.getElementById('search-equipment-selected-container');
    const selectedCountElement = document.getElementById('search-equipment-selected-count');
    const modalElement = document.getElementById('search-equipment-modal');

    if(checkboxAllEquipment === null || buttonSelectEquipment === null || selectedCountContainer === null || selectedCountElement === null)
    {
        return;
    }

    const selection = createEquipmentSelection({
        equipmentContainerId: 'search-equipment',
        hiddenInputsContainerId: 'search-equipment-hidden-inputs',
        onSelectionChanged: function(selectedIds)
        {
            selectedCountElement.textContent = selectedIds.length;
            selectedCountContainer.classList.toggle('text-bg-secondary', selectedIds.length === 0);
            selectedCountContainer.classList.toggle('text-bg-success', selectedIds.length > 0);
        }
    });

    if(selection === null)
    {
        return;
    }

    function toggleEquipmentControls()
    {
        const isAllEquipmentSelected = checkboxAllEquipment.checked;
        buttonSelectEquipment.disabled = isAllEquipmentSelected;
        selectedCountContainer.classList.toggle('opacity-50', isAllEquipmentSelected);
    }

    checkboxAllEquipment.addEventListener('click', toggleEquipmentControls);
    toggleEquipmentControls();

    if(modalElement !== null)
    {
        modalElement.addEventListener('show.bs.modal', selection.updateCards);
    }
});

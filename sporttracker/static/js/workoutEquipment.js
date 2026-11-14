document.addEventListener('DOMContentLoaded', function()
{
    const equipmentContainer = document.getElementById('workout-equipment');
    const selectedCountContainer = document.getElementById('workout-equipment-selected-container');
    const selectedCountElement = document.getElementById('workout-equipment-selected-count');
    const modalElement = document.getElementById('workout-equipment-modal');

    const selection = createEquipmentSelection({
        equipmentContainerId: 'workout-equipment',
        hiddenInputsContainerId: 'workout-equipment-hidden-inputs',
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

    const presetButtons = equipmentContainer.querySelectorAll('.workout-equipment-preset');
    for(const presetButton of presetButtons)
    {
        presetButton.addEventListener('click', function()
        {
            const equipmentIds = presetButton.dataset.equipmentIds.length > 0
                ? presetButton.dataset.equipmentIds.split(',')
                : [];

            selection.setSelection(equipmentIds);

            const dropdown = presetButton.closest('.dropdown');
            if(dropdown !== null)
            {
                const dropdownToggle = dropdown.querySelector('[data-bs-toggle="dropdown"]');
                if(dropdownToggle !== null && window.bootstrap)
                {
                    window.bootstrap.Dropdown.getOrCreateInstance(dropdownToggle).hide();
                }
            }
        });
    }

    if(modalElement !== null)
    {
        modalElement.addEventListener('show.bs.modal', selection.updateCards);
    }
});

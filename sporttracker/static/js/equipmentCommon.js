function createEquipmentSelection(options)
{
    const equipmentContainer = document.getElementById(options.equipmentContainerId);
    const hiddenInputsContainer = document.getElementById(options.hiddenInputsContainerId);

    if(equipmentContainer === null || hiddenInputsContainer === null)
    {
        return null;
    }

    const cards = equipmentContainer.querySelectorAll('.equipment-modal-card');
    const onSelectionChanged = options.onSelectionChanged || function() {};

    function findHiddenInput(equipmentId)
    {
        for(const input of hiddenInputsContainer.querySelectorAll('input[name="equipment_ids"]'))
        {
            if(input.value === equipmentId)
            {
                return input;
            }
        }

        return null;
    }

    function getSelectedIds()
    {
        return Array.from(hiddenInputsContainer.querySelectorAll('input[name="equipment_ids"]')).map(function(input)
        {
            return input.value;
        });
    }

    function createHiddenInput(equipmentId)
    {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'equipment_ids';
        input.value = equipmentId;
        hiddenInputsContainer.appendChild(input);
    }

    function updateCards()
    {
        const selectedIds = new Set(getSelectedIds());

        for(const card of cards)
        {
            const icon = card.querySelector('.equipment-select-icon');
            icon.dataset.selected = selectedIds.has(card.dataset.equipmentId);
            icon.classList.toggle('bg-secondary', !selectedIds.has(card.dataset.equipmentId));
            icon.classList.toggle('bg-success', selectedIds.has(card.dataset.equipmentId));
        }
    }

    function clearSelection()
    {
        hiddenInputsContainer.innerHTML = '';
    }

    function setSelection(equipmentIds)
    {
        clearSelection();

        const uniqueIds = new Set(equipmentIds);

        for(const equipmentId of uniqueIds)
        {
            createHiddenInput(equipmentId);
        }

        updateCards();
        onSelectionChanged(getSelectedIds());
    }

    function toggleEquipmentFromCard(card)
    {
        const equipmentId = card.dataset.equipmentId;

        const hiddenInput = findHiddenInput(equipmentId);
        if(hiddenInput === null)
        {
            createHiddenInput(equipmentId);
        }
        else
        {
            hiddenInput.remove();
        }

        updateCards();
        onSelectionChanged(getSelectedIds());
    }

    for(const card of cards)
    {
        card.addEventListener('click', function()
        {
            toggleEquipmentFromCard(card);
        });

        card.addEventListener('keydown', function(event)
        {
            if(event.key === 'Enter' || event.key === ' ')
            {
                event.preventDefault();
                toggleEquipmentFromCard(card);
            }
        });
    }

    updateCards();
    onSelectionChanged(getSelectedIds());

    return {
        getSelectedIds: getSelectedIds,
        updateCards: updateCards,
        clearSelection: clearSelection,
        setSelection: setSelection
    };
}

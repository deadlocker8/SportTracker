document.addEventListener('DOMContentLoaded', function()
{
    const equipmentContainer = document.getElementById('equipment-preset-equipment');
    const hiddenInputsContainer = document.getElementById('equipment-preset-hidden-inputs');

    if(equipmentContainer === null || hiddenInputsContainer === null)
    {
        return;
    }

    const cards = equipmentContainer.querySelectorAll('.equipment-modal-card');

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

    function toggleEquipmentFromCard(card)
    {
        const equipmentId = card.dataset.equipmentId;

        let hiddenInput = findHiddenInput(equipmentId);
        if(hiddenInput === null)
        {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'equipment_ids';
            input.value = equipmentId;
            hiddenInputsContainer.appendChild(input);
        }
        else
        {
            hiddenInput.remove();
        }

        updateCards();
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
});

const workoutTypeSelect = document.getElementById('maintenance-event-type');
const customWorkoutFieldSelect = document.getElementById('maintenance-event-custom-field');
const customWorkoutFieldValueSelect = document.getElementById('maintenance-event-custom-field-value');
const equipmentTypeSelect = document.getElementById('maintenance-event-equipment-type');
const equipmentSelect = document.getElementById('maintenance-event-equipment');

init();


function init()
{
    workoutTypeSelect.addEventListener('change', function(e)
    {
        updateAllCustomWorkoutFieldSelects();
        updateEquipmentTypeSelect();
        updateEquipmentSelect();
    });

    customWorkoutFieldSelect.addEventListener('change', function(e)
    {
        updateCustomWorkoutFieldSelect(customWorkoutFieldValueSelect, (item) =>
        {
            return item.dataset.workoutType === workoutTypeSelect.value && item.dataset.fieldId === customWorkoutFieldSelect.value;
        });

        if(customWorkoutFieldSelect.value !== '')
        {
            resetEquipmentSelects();
        }
    });

    equipmentTypeSelect.addEventListener('change', function(e)
    {
        if(equipmentTypeSelect.value !== '')
        {
            resetCustomWorkoutFieldSelects();
        }

        updateEquipmentSelect();
    });

    equipmentSelect.addEventListener('change', function(e)
    {
        if(equipmentSelect.value !== '')
        {
            resetCustomWorkoutFieldSelects();
        }
    });

    updateAllCustomWorkoutFieldSelects();
    updateEquipmentTypeSelect();
    updateEquipmentSelect();
    initialSelect();
}

function updateAllCustomWorkoutFieldSelects()
{
    updateCustomWorkoutFieldSelect(customWorkoutFieldSelect, (item) =>
    {
        return item.dataset.workoutType === workoutTypeSelect.value || item.classList.contains('maintenance-event-custom-field-select-placeholder');
    });

    updateCustomWorkoutFieldSelect(customWorkoutFieldValueSelect, (item) =>
    {
        return item.dataset.workoutType === workoutTypeSelect.value && item.dataset.fieldId === customWorkoutFieldSelect.value;
    });
}

function updateEquipmentTypeSelect()
{
    const availableEquipmentTypes = new Set();
    equipmentSelect.querySelectorAll('option').forEach((item) =>
    {
        if(item.value !== '' && item.dataset.workoutType === workoutTypeSelect.value)
        {
            availableEquipmentTypes.add(item.dataset.equipmentType);
        }
    });

    updateCustomWorkoutFieldSelect(equipmentTypeSelect, (item) =>
    {
        return item.classList.contains('maintenance-event-equipment-type-select-placeholder') || availableEquipmentTypes.has(item.value);
    });
}

function updateEquipmentSelect()
{
    updateCustomWorkoutFieldSelect(equipmentSelect, (item) =>
    {
        return item.classList.contains('maintenance-event-equipment-select-placeholder') ||
            (item.dataset.workoutType === workoutTypeSelect.value && item.dataset.equipmentType === equipmentTypeSelect.value);
    });
}

function resetEquipmentSelects()
{
    equipmentTypeSelect.value = '';
    updateEquipmentSelect();
}

function resetCustomWorkoutFieldSelects()
{
    customWorkoutFieldSelect.value = '';
    updateCustomWorkoutFieldSelect(customWorkoutFieldValueSelect, (item) =>
    {
        return item.dataset.workoutType === workoutTypeSelect.value && item.dataset.fieldId === customWorkoutFieldSelect.value;
    });
}

function initialSelect()
{
    customWorkoutFieldSelect.value = initialCustomFieldId;
    customWorkoutFieldSelect.dispatchEvent(new Event('change', { 'bubbles': true }));
    customWorkoutFieldValueSelect.value = initialCustomFieldValue;

    if(initialEquipmentId !== '')
    {
        const selectedEquipmentOption = equipmentSelect.querySelector(`option[value="${initialEquipmentId}"]`);
        if(selectedEquipmentOption)
        {
            equipmentTypeSelect.value = selectedEquipmentOption.dataset.equipmentType;
            updateEquipmentSelect();
            equipmentSelect.value = initialEquipmentId;
        }
    }
}

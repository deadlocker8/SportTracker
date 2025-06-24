const workoutTypeSelect = document.getElementById('maintenance-event-type');
const customWorkoutFieldSelect = document.getElementById('maintenance-event-custom-field');
const customWorkoutFieldValueSelect = document.getElementById('maintenance-event-custom-field-value');

init();


function init()
{
    workoutTypeSelect.addEventListener('change', function(e)
    {
        updateAllCustomWorkoutFieldSelects();
    });

    customWorkoutFieldSelect.addEventListener('change', function(e)
    {
        updateCustomWorkoutFieldSelect(customWorkoutFieldValueSelect, (item) =>
        {
            return item.dataset.workoutType === workoutTypeSelect.value && item.dataset.fieldId === customWorkoutFieldSelect.value;
        });
    });

    updateAllCustomWorkoutFieldSelects();
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

function initialSelect()
{
    customWorkoutFieldSelect.value = initialCustomFieldId;
    customWorkoutFieldSelect.dispatchEvent(new Event('change', { 'bubbles': true }));
    customWorkoutFieldValueSelect.value = initialCustomFieldValue;
}
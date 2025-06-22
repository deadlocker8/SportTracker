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

function updateCustomWorkoutFieldSelect(select, itemFilter)
{
    let options = select.querySelectorAll('option');
    let matchingOptions = [];
    options.forEach((item) =>
    {
        let isMatching = itemFilter(item);
        item.classList.toggle('hidden', !isMatching);
        if(isMatching)
        {
            matchingOptions.push(item);
        }
    });

    // no matching options or single matching option is the placeholder with empty value
    if(matchingOptions.length === 0 || matchingOptions.length === 1  && matchingOptions[0].value === '')
    {
        select.value = '';
        select.disabled = true;
    }
    else
    {
        select.value = matchingOptions[0].value;
        select.disabled = false;
    }
}

function initialSelect()
{
    customWorkoutFieldSelect.value = initialCustomFieldId;
    customWorkoutFieldValueSelect.value = initialCustomFieldValue;

    customWorkoutFieldSelect.dispatchEvent(new Event('change', { 'bubbles': true }));
}
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
            return item.dataset.workoutType === workoutTypeSelect.value && item.dataset.fieldName === customWorkoutFieldSelect.value;
        });
    });

    updateAllCustomWorkoutFieldSelects();
}

function updateAllCustomWorkoutFieldSelects()
{
    updateCustomWorkoutFieldSelect(customWorkoutFieldSelect, (item) =>
    {
        return item.dataset.workoutType === workoutTypeSelect.value || item.classList.contains('maintenance-event-custom-field-select-placeholder');
    });

    updateCustomWorkoutFieldSelect(customWorkoutFieldValueSelect, (item) =>
    {
        return item.dataset.workoutType === workoutTypeSelect.value && item.dataset.fieldName === customWorkoutFieldSelect.value;
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

    if(matchingOptions.length === 0)
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
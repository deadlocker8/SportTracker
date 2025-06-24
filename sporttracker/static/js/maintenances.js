const customWorkoutFieldSelect = document.getElementById('customWorkoutFieldId');
const customWorkoutFieldValueSelect = document.getElementById('customWorkoutFieldValue');

init();


function init()
{
    customWorkoutFieldSelect.addEventListener('change', function(e)
    {
        updateAllCustomWorkoutFieldSelects();
    });

    updateAllCustomWorkoutFieldSelects();
    initialSelect();
}

function updateAllCustomWorkoutFieldSelects()
{
    updateCustomWorkoutFieldSelect(customWorkoutFieldValueSelect, (item) =>
    {
        return item.dataset.fieldId === customWorkoutFieldSelect.value;
    });
}

function initialSelect()
{
    customWorkoutFieldSelect.value = initialCustomFieldId;
    customWorkoutFieldSelect.dispatchEvent(new Event('change', { 'bubbles': true }));
    customWorkoutFieldValueSelect.value = initialCustomFieldValue;
}
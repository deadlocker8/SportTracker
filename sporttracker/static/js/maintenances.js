const workoutTypeSelect = document.getElementById('maintenance-event-type');
const customWorkoutFieldSelect = document.getElementById('maintenance-event-custom-field');

init();


function init()
{
    workoutTypeSelect.addEventListener('change', function(e)
    {
        clearCustomWorkoutFields();
        updateCustomWorkoutFields();
    });

    clearCustomWorkoutFields();
    updateCustomWorkoutFields();
}

function clearCustomWorkoutFields()
{
    let options = customWorkoutFieldSelect.querySelectorAll('option');
    options.forEach((item) => {
        item.classList.toggle('hidden', true);
    });
}

function updateCustomWorkoutFields()
{
    let options = customWorkoutFieldSelect.querySelectorAll('option[data-workout-type="' + workoutTypeSelect.value + '"]');
    options.forEach((item) => {
        item.classList.toggle('hidden', false);
    });

    if(options.length > 0)
    {
        customWorkoutFieldSelect.value = options[0].value;
    }
}
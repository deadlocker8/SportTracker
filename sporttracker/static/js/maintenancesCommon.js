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
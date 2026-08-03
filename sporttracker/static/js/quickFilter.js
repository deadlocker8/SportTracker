document.addEventListener('DOMContentLoaded', function()
{
    const modeYears = document.getElementById('quickFilterModeYears');
    const modeDateRange = document.getElementById('quickFilterModeDateRange');
    const sectionYears = document.getElementById('quickFilterYearsSection');
    const sectionDateRange = document.getElementById('quickFilterDateRangeSection');
    const dateFrom = document.getElementById('quickFilterDateFrom');
    const dateTo = document.getElementById('quickFilterDateTo');

    function toggleSections()
    {
        const isDateMode = modeDateRange.checked;
        sectionYears.classList.toggle('d-none', isDateMode);
        sectionDateRange.classList.toggle('d-none',!isDateMode);
        dateFrom.required = isDateMode;
        dateTo.required = isDateMode;
    }

    modeYears.addEventListener('change', toggleSections);
    modeDateRange.addEventListener('change', toggleSections);

    function updateDateValidation()
    {
        dateTo.min = dateFrom.value;
        dateFrom.max = dateTo.value;
    }

    dateFrom.addEventListener('change', updateDateValidation);
    dateTo.addEventListener('change', updateDateValidation);

    toggleSections();
    updateDateValidation();
});

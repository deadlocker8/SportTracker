document.addEventListener('DOMContentLoaded', function()
{
    Mousetrap.bind('left', function()
    {
        document.getElementById('month-select-previous').click();
    });

    Mousetrap.bind('right', function()
    {
        document.getElementById('month-select-next').click();
    });

    Mousetrap.bind('0', function()
    {
        document.getElementById('month-select-current').click();
    });

    let selectedYear;

    let buttonsSelectYear = document.getElementsByClassName('btn-select-year');
    for(let i = 0; i < buttonsSelectYear.length; i++)
    {
        buttonsSelectYear[i].addEventListener('click', function() {
            selectedYear = this.dataset.year;
        });
    }

    let buttonsSelectMonth = document.getElementsByClassName('btn-select-month');
    for(let i = 0; i < buttonsSelectMonth.length; i++)
    {
        buttonsSelectMonth[i].addEventListener('click', function() {
            let month = this.dataset.month;
            let baseUrl = document.getElementById('modalMonthSelect').dataset.url
            console.log(baseUrl);
            window.location = baseUrl + selectedYear + '/' + month;
        });
    }
});
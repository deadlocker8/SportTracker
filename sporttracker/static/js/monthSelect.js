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
});
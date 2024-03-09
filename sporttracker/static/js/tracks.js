document.addEventListener('DOMContentLoaded', function()
{
    let touchStartX = 0;
    let touchEndX = 0;
    let touchStartY = 0;
    let touchEndY = 0;
    const THRESHOLD = 100;

    document.addEventListener('touchstart', e =>
    {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    })

    document.addEventListener('touchend', e =>
    {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;

        if(Math.abs(touchStartY - touchEndY) > THRESHOLD)
        {
            return;
        }

        if(touchEndX < touchStartX - THRESHOLD)
        {
            document.getElementById('month-select-next').click();
        }
        if(touchEndX > touchStartX + THRESHOLD)
        {
            document.getElementById('month-select-previous').click();
        }
    })
});
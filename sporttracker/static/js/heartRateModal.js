document.addEventListener('DOMContentLoaded', function()
{
    let buttonsHeartRateModal = document.querySelectorAll('.button-heart-rate-modal');
    for(let i = 0; i < buttonsHeartRateModal.length; i++)
    {
        buttonsHeartRateModal[i].addEventListener('click', function()
        {
            const workoutId = buttonsHeartRateModal[i].dataset.workoutId;
            const chartContainer = document.getElementById('heart-rate-chart-container-' + workoutId);
            chartContainer.innerHTML = '';
            const progressSpinner = document.getElementById('heart-rate-modal-progress-spinner-' + workoutId);
            progressSpinner.classList.toggle('hidden', false);

            const modal = document.getElementById('heart-rate-modal-' + workoutId);
            modal.addEventListener('shown.bs.modal', event => {
                const url = buttonsHeartRateModal[i].dataset.url;
                let xhr = new XMLHttpRequest();
                xhr.open('GET', url);
                xhr.onload = function()
                {
                    if(xhr.status === 200)
                    {
                        let response = JSON.parse(xhr.response);
                        createHeartRateChart(chartContainer, response);
                        progressSpinner.classList.toggle('hidden', true);
                    }
                };
                xhr.send();
            })
            new bootstrap.Modal(modal).show();
        });
    }
});

function createHeartRateChart(chartContainer, response)
{
    const data = [
        {
            x: response.timestamps,
            y: response.values,
            type: 'scatter',
            marker: {
                color: '#FF0000'
            },
        },
    ];

    const plotlyLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: {
            type: 'date',
            color: '#FFFFFF',
            automargin: true,
            showgrid: false,
        },
        yaxis: {
            title: {
                text: 'BPM',
            },
            rangemode: 'tozero',
            tickformat: '.0f',
            showline: true,
            color: '#FFFFFF'
        },
        barmode: 'group',
        legend: {
            font: {
                color: '#FFFFFF'
            }
        }
    }

    const plotlyConfig = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot(chartContainer, data, plotlyLayout, plotlyConfig);
}
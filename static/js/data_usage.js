document.getElementById('track-data-usage-btn').addEventListener('click', function() {
    fetch('/track-data-usage', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.data_usage) {
            // Update download and upload MBs
            document.getElementById('download-usage').textContent = data.data_usage.download;
            document.getElementById('upload-usage').textContent = data.data_usage.upload;

            // Update the chart data with new download and upload values, passing the timestamp
            updateChart(data.data_usage.timestamp, data.data_usage.download, data.data_usage.upload);
        } else {
            console.error('Unexpected data format', data);
        }
    })
    .catch(error => {
        console.error('Error tracking data usage:', error);
    });
});

// Initialize chart with Chart.js
const ctx = document.getElementById('dataUsageChart').getContext('2d');
let dataUsageChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // Labels will be dynamically updated
        datasets: [
            {
                label: 'Download (MB)',
                data: [],
                borderColor: '#00d8ff',
                backgroundColor: 'rgba(0, 216, 255, 0.2)',
                fill: true,
                tension: 0.3
            },
            {
                label: 'Upload (MB)',
                data: [],
                borderColor: '#ff6384',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                fill: true,
                tension: 0.3
            }
        ]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'MB'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Day and Time'
                }
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        // Format the label to include the time
                        let label = tooltipItem.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        label += `${tooltipItem.raw} MB`;
                        return label;
                    },
                    title: function(tooltipItems) {
                        const timestamp = tooltipItems[0].label;
                        // Convert ISO timestamp to 12-hour format with AM/PM
                        const date = new Date(timestamp);
                        let hours = date.getHours();
                        const minutes = date.getMinutes().toString().padStart(2, '0');
                        const ampm = hours >= 12 ? 'PM' : 'AM';
                        hours = hours % 12 || 12; // Convert to 12-hour format

                        return `${date.toDateString()} ${hours}:${minutes} ${ampm}`;
                    }
                }
            }
        }
    }
});

// Function to update the chart with new data
function updateChart(timestamp, download, upload) {
    // Add new data to chart
    dataUsageChart.data.labels.push(timestamp);
    dataUsageChart.data.datasets[0].data.push(download);
    dataUsageChart.data.datasets[1].data.push(upload);
    dataUsageChart.update(); // Refresh chart
}

document.getElementById('run-speedtest').addEventListener('click', function () {
    const runButton = document.getElementById('run-speedtest');
    const resultsContainer = document.getElementById('speedtest-results');
    const resultMessage = document.getElementById('speedtest-result');
    const pingDisplay = document.getElementById('ping');

    // Add loading state to the button
    runButton.classList.add('loading');
    runButton.disabled = true;

    // Hide previous results
    resultsContainer.style.display = 'none';
    resultMessage.textContent = '';

    // Simulate API call or speed test logic
    fetch('/api/run-speed-test') // Adjust for your Flask route
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                resultMessage.textContent = `Error: ${data.message}`;
            } else {
                // Update results on success
                pingDisplay.textContent = `${data.results.ping} ms`;
                downloadGauge.refresh(data.results.download_speed);
                uploadGauge.refresh(data.results.upload_speed);

                // Show results container
                resultsContainer.style.display = 'block';
            }
        })
        .catch(error => {
            resultMessage.textContent =
                'An error occurred while running the speed test. Please try again later.';
            console.error('Speed test error:', error);
        })
        .finally(() => {
            // Remove loading state from the button
            runButton.classList.remove('loading');
            runButton.disabled = false;
        });
});

// Initialize JustGage for the gauges
const downloadGauge = new JustGage({
    id: 'download-speedometer',
    value: 0,
    min: 0,
    max: 1000, // Adjust the max value based on your requirements
    title: 'Download Speed',
    label: 'Mbps',
});

const uploadGauge = new JustGage({
    id: 'upload-speedometer',
    value: 0,
    min: 0,
    max: 500, // Adjust the max value based on your requirements
    title: 'Upload Speed',
    label: 'Mbps',
});

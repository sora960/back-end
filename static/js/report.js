document.getElementById('generate-report-btn').addEventListener('click', function() {
    const reportType = document.getElementById('report-type').value;

    // Get start and end date and convert to ISO format, but only use the date part (YYYY-MM-DD)
    const startDateInput = document.getElementById('start-date').value;
    const endDateInput = document.getElementById('end-date').value;

    // Convert to YYYY-MM-DD format, or handle missing input gracefully
    const startDate = startDateInput ? new Date(startDateInput).toISOString().split('T')[0] : null;
    const endDate = endDateInput ? new Date(endDateInput).toISOString().split('T')[0] : null;

    if (!reportType || !startDate || !endDate) {
        // Handle missing inputs before making the request
        document.getElementById('report-output').innerHTML = '<p>Please select all required fields (Report Type, Start Date, End Date).</p>';
        return;
    }

    // Send POST request to generate report
    fetch('/generate_report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            report_type: reportType,
            start_date: startDate,
            end_date: endDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.report_data && data.report_data.length > 0) {
            // Set up report title
            let reportContent = `<h2>${reportType} Report</h2>`;

            // Create table structure based on the report type
            reportContent += `
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            ${reportType === "IP Allocation" ? '<th>IP Address</th><th>Device Name</th>' : ''}
                            ${reportType === "Data Usage" ? '<th>Download (MB)</th><th>Upload (MB)</th>' : ''}
                            ${reportType === "Speed Test" ? '<th>Ping (ms)</th><th>Download Speed (Mbps)</th><th>Upload Speed (Mbps)</th>' : ''}
                        </tr>
                    </thead>
                    <tbody>
            `;

            // Loop through each item in the report data
            data.report_data.forEach(item => {
                const dateTime = new Date(item.timestamp);
                const date = dateTime.toLocaleDateString();
                const time = dateTime.toLocaleTimeString();

                reportContent += `<tr><td>${date}</td><td>${time}</td>`;

                // Check for the report type and add appropriate table columns
                if (reportType === "IP Allocation") {
                    reportContent += `<td>${item.ip_address || 'N/A'}</td><td>${item.device_name || 'N/A'}</td>`;
                } else if (reportType === "Data Usage") {
                    reportContent += `<td>${item.download || 'N/A'}</td><td>${item.upload || 'N/A'}</td>`;
                } else if (reportType === "Speed Test") {
                    reportContent += `<td>${item.ping || 'N/A'}</td><td>${item.download_speed || 'N/A'}</td><td>${item.upload_speed || 'N/A'}</td>`;
                }

                reportContent += `</tr>`;
            });

            reportContent += '</tbody></table>';
            document.getElementById('report-output').innerHTML = reportContent;
        } else {
            // Display message when no data is found
            document.getElementById('report-output').innerHTML = '<p>No data available for the selected range.</p>';
        }
    })
    .catch(error => {
        console.error('Error generating report:', error);
        document.getElementById('report-output').innerHTML = '<p>Error generating report.</p>';
    });
});

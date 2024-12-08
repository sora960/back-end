document.addEventListener("DOMContentLoaded", function () {
    console.log("Page loaded. Ensuring spinner is hidden.");
    hideLoadingSpinner(); // Ensure spinner is hidden on page load
    fetchDashboardData(); // Fetch and populate the dashboard data
});

// Unified function for API calls
async function fetchAPI(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    try {
        const response = await fetch(endpoint, options);
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || data.error || 'API error');
        return data;
    } catch (error) {
        console.error(`Error during API call to ${endpoint}:`, error);
        throw error;
    }
}

// Main function to fetch and populate dashboard data
async function fetchDashboardData() {
    try {
        console.log("Showing spinner...");
        showLoadingSpinner(); // Show spinner before API call

        const dashboardData = await fetchAPI('/dashboard_data'); // Fetch dashboard data
        console.log("Fetched Dashboard Data:", dashboardData); // Debugging log

        // Populate the dashboard UI with fetched data
        populateQuickSummary(dashboardData.quick_summary || {});
        populateSpeedTestHistory(dashboardData.speed_test_history || []);
        populateDataUsageHistory(dashboardData.data_usage_history || []);
        populateRecentActivity(dashboardData.recent_activity || []);
        populateNetworkInfo(
            dashboardData.your_ip || "N/A",
            dashboardData.public_ip || "Unavailable",
            dashboardData.network_provider || "Unknown ISP"
        );
    } catch (error) {
        console.error("Error fetching dashboard data:", error);
        showResponse(`Error fetching dashboard data: ${error.message}`, 'danger');
    } finally {
        hideLoadingSpinner(); // Always hide spinner after API call
        console.log("Spinner hidden.");
    }
}

// Function to populate quick summary data
function populateQuickSummary(quickSummary) {
    console.log("Populating Quick Summary Data:", quickSummary);
    document.getElementById('available-ip').textContent = quickSummary.available_ips || "N/A";
    document.getElementById('occupied-ip').textContent = quickSummary.allocated_ips || "N/A";
}

// Function to populate speed test history
function populateSpeedTestHistory(speedTestHistory) {
    console.log("Populating Speed Test History Data:", speedTestHistory);

    const chartData = {
        labels: speedTestHistory.map(entry => new Date(entry.timestamp).toLocaleString()),
        datasets: [
            {
                label: 'Download Speed (Mbps)',
                data: speedTestHistory.map(entry => entry.download_speed),
                borderColor: '#40c9ff', // Updated to softer cyan
                backgroundColor: 'rgba(64, 201, 255, 0.1)', // Transparent fill
                fill: true,
            },
            {
                label: 'Upload Speed (Mbps)',
                data: speedTestHistory.map(entry => entry.upload_speed),
                borderColor: '#6cd3b0', // Updated to muted mint green
                backgroundColor: 'rgba(108, 211, 176, 0.1)', // Transparent fill
                fill: true,
            },
        ],
    };

    const ctx = document.getElementById('speedTestChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#a6b0bf', // Updated legend text color
                        font: { family: "'Poppins', sans-serif", size: 14 },
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#a6b0bf' }, // Updated axis label color
                    grid: { color: '#3a3f50' }, // Updated gridline color
                    title: { display: true, text: 'Time', color: '#a6b0bf' },
                },
                y: {
                    ticks: { color: '#a6b0bf' },
                    grid: { color: '#3a3f50' },
                    title: { display: true, text: 'Speed (Mbps)', color: '#a6b0bf' },
                },
            },
        },
    });
}

// Function to populate data usage history
function populateDataUsageHistory(dataUsageHistory) {
    console.log("Populating Data Usage History Data:", dataUsageHistory);

    const chartData = {
        labels: dataUsageHistory.map(entry => entry.day),
        datasets: [
            {
                label: 'Download (MB)',
                data: dataUsageHistory.map(entry => entry.download),
                backgroundColor: '#2094d1', // Updated to darker cyan
                borderWidth: 1,
            },
            {
                label: 'Upload (MB)',
                data: dataUsageHistory.map(entry => entry.upload),
                backgroundColor: '#3aa57c', // Updated to muted green
                borderWidth: 1,
            },
        ],
    };

    const ctx = document.getElementById('dataUsageChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#a6b0bf', // Updated legend text color
                        font: { family: "'Poppins', sans-serif", size: 14 },
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#a6b0bf' },
                    grid: { color: '#3a3f50' },
                    title: { display: true, text: 'Day', color: '#a6b0bf' },
                },
                y: {
                    ticks: { color: '#a6b0bf' },
                    grid: { color: '#3a3f50' },
                    title: { display: true, text: 'Data (MB)', color: '#a6b0bf' },
                },
            },
        },
    });
}


// Function to populate recent activity
function populateRecentActivity(recentActivity) {
    console.log("Populating Recent Activity Data:", recentActivity);

    const activityList = document.getElementById('recent-activity-list');
    activityList.innerHTML = ''; // Clear any existing content

    if (!recentActivity.length) {
        activityList.innerHTML = '<li class="text-center">No recent activity found.</li>';
        return;
    }

    recentActivity.forEach(activity => {
        const listItem = document.createElement('li');
        listItem.textContent = `${new Date(activity.timestamp).toLocaleString()} - ${activity.action}: ${activity.details}`;
        activityList.appendChild(listItem);
    });
}

// Function to populate network information
function populateNetworkInfo(localIP, publicIP, networkProvider) {
    console.log("Populating Network Info:", { localIP, publicIP, networkProvider });
    document.getElementById('your-ip').textContent = localIP;
    document.getElementById('network-provider').textContent = networkProvider || 'Unknown ISP';
}

// Show the loading spinner
function showLoadingSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.classList.remove('d-none');
}

// Hide the loading spinner
function hideLoadingSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.classList.add('d-none');
}

// Show response messages
function showResponse(message, type) {
    const responseEl = document.getElementById('response');
    if (responseEl) {
        responseEl.textContent = message;
        responseEl.className = `alert alert-${type}`;
        responseEl.classList.remove('d-none');

        setTimeout(() => responseEl.classList.add('d-none'), 5000);
    }
}

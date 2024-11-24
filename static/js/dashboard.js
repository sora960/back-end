window.onload = function () {
    fetch('/api/dashboard_data')
        .then(response => response.json())
        .then(dashboardData => {
            // IP Status Pie Chart
            var ipStatusCtx = document.getElementById('ipStatusChart').getContext('2d');
            new Chart(ipStatusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Allocated', 'Available'],
                    datasets: [{
                        data: [dashboardData.ip_status.allocated_ip, dashboardData.ip_status.available_ip],
                        backgroundColor: ['#00d8ff', '#a8a8ff'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#ffffff'
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    let percentage = ((context.raw / dashboardData.ip_status.total_ip) * 100).toFixed(2);
                                    return `${context.label}: ${percentage}%`;
                                }
                            }
                        },
                        datalabels: {
                            formatter: (value, ctx) => {
                                let total = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                let percentage = ((value / total) * 100).toFixed(2) + "%";
                                return percentage;
                            },
                            color: '#ffffff',
                            font: {
                                weight: 'bold',
                                size: 16,  // Increase size for better visibility
                            },
                            anchor: 'center',  // Center the text inside the chart
                            align: 'center',  // Center alignment
                        }
                    }
                }
            });

            // Format date to a readable format for the speed test chart
            function formatDate(dateString) {
                const date = new Date(dateString);
                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                });
            }

            // Speed Test History Line Chart
            var speedTestCtx = document.getElementById('speedTestChart').getContext('2d');
            new Chart(speedTestCtx, {
                type: 'line',
                data: {
                    labels: dashboardData.speed_test_history.map(test => formatDate(test.timestamp || "No Data")),
                    datasets: [{
                        label: 'Download Speed',
                        data: dashboardData.speed_test_history.map(test => test.download_speed),
                        borderColor: '#00d8ff',
                        backgroundColor: 'rgba(0, 216, 255, 0.2)',  // Add a bit of fill for a modern look
                        tension: 0.4,  // Make the lines curved
                        fill: true,  // Fill the area under the curve
                    }, {
                        label: 'Upload Speed',
                        data: dashboardData.speed_test_history.map(test => test.upload_speed),
                        borderColor: '#a8a8ff',
                        backgroundColor: 'rgba(168, 168, 255, 0.2)',  // Add a bit of fill for a modern look
                        tension: 0.4,  // Make the lines curved
                        fill: true,  // Fill the area under the curve
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            display: false,  // This hides the x-axis labels
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: '#3b3b5f'  // Adjust the color of the grid lines
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                color: '#00d8ff',  // Make the labels color pop
                            }
                        }
                    }
                }
            });

            // Data Usage History Bar Chart
            var dataUsageCtx = document.getElementById('dataUsageChart').getContext('2d');
            new Chart(dataUsageCtx, {
                type: 'bar',
                data: {
                    labels: dashboardData.data_usage_history.map(usage => usage.day),
                    datasets: [{
                        label: 'Download',
                        data: dashboardData.data_usage_history.map(usage => usage.download),
                        backgroundColor: '#00d8ff'
                    }, {
                        label: 'Upload',
                        data: dashboardData.data_usage_history.map(usage => usage.upload),
                        backgroundColor: '#a8a8ff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,  // Prevents overflow in small areas
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    }
                }
            });

            // Update the text values for the Quick Summary
            document.getElementById('total-ip').textContent = `Total IP: ${dashboardData.quick_summary.total_ips}`;
            document.getElementById('available-ip').textContent = `Available IP: ${dashboardData.quick_summary.available_ips}`;
            document.getElementById('allocated-ip').textContent = `Allocated IP: ${dashboardData.quick_summary.allocated_ips}`;

            // Populate Recent Activity
            let activityLog = document.getElementById('recent-activity-list');
            activityLog.innerHTML = '';
            dashboardData.recent_activity.forEach(activity => {
                let li = document.createElement('li');
                li.textContent = `${activity.action} - ${activity.details} (${formatDate(activity.timestamp)})`;
                activityLog.appendChild(li);
            });

            document.getElementById('your-ip').textContent = dashboardData.your_ip;
            document.getElementById('network-provider').textContent = dashboardData.network_provider;
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            document.getElementById('total-ip').textContent = 'Error loading data';
            document.getElementById('available-ip').textContent = 'Error loading data';
            document.getElementById('allocated-ip').textContent = 'Error loading data';
            document.getElementById('your-ip').textContent = 'Error loading IP';
        });
};

document.addEventListener("DOMContentLoaded", async function () {
    const reportsTableBody = document.querySelector("#reports-table tbody");
    const errorDiv = document.querySelector("#error-message");
    const reportTypeFilter = document.querySelector("#report-type-filter");
    const dateFilter = document.querySelector("#date-filter");
    const customDateRange = document.querySelector("#custom-date-range");
    const startDateInput = document.querySelector("#start-date");
    const endDateInput = document.querySelector("#end-date");
    const exportPdfButton = document.querySelector("#export-pdf");

    let allReports = []; // Store all reports to filter locally

    try {
        // Run migration to ensure the latest reports are available
        await runMigration();
        console.log("Migration completed successfully.");

        // Fetch and display reports
        allReports = await fetchReports();
        populateReportsTable(allReports); // Initially populate with all reports

        // Event listeners for filters
        reportTypeFilter.addEventListener("change", applyFilters);
        dateFilter.addEventListener("change", handleDateFilterChange);
        startDateInput.addEventListener("change", applyFilters);
        endDateInput.addEventListener("change", applyFilters);

        // Event listener for Export to PDF
        exportPdfButton.addEventListener("click", exportToPdf);

        function handleDateFilterChange() {
            const selectedOption = dateFilter.value;

            if (selectedOption === "custom") {
                customDateRange.style.display = "block";
            } else {
                customDateRange.style.display = "none";
                applyFilters();
            }
        }

        function applyFilters() {
            let filteredReports = allReports;

            // Apply Report Type Filter
            const selectedType = reportTypeFilter.value;
            if (selectedType) {
                filteredReports = filteredReports.filter(report => report.report_type === selectedType);
            }

            // Apply Date Range Filter
            const selectedDateOption = dateFilter.value;
            const today = new Date();
            const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
            const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

            if (selectedDateOption === "today") {
                filteredReports = filteredReports.filter(report => isSameDay(new Date(report.time_and_date), new Date()));
            } else if (selectedDateOption === "week") {
                filteredReports = filteredReports.filter(report => new Date(report.time_and_date) >= startOfWeek);
            } else if (selectedDateOption === "month") {
                filteredReports = filteredReports.filter(report => new Date(report.time_and_date) >= startOfMonth);
            } else if (selectedDateOption === "custom") {
                const startDate = new Date(startDateInput.value);
                const endDate = new Date(endDateInput.value);
                filteredReports = filteredReports.filter(report => {
                    const reportDate = new Date(report.time_and_date);
                    return reportDate >= startDate && reportDate <= endDate;
                });
            }

            // Populate the table with the filtered reports
            populateReportsTable(filteredReports);
        }

        function isSameDay(date1, date2) {
            return date1.getDate() === date2.getDate() &&
                date1.getMonth() === date2.getMonth() &&
                date1.getFullYear() === date2.getFullYear();
        }

        /**
         * Run migration to ensure the latest reports are available
         */
        async function runMigration() {
            const response = await fetch("/run_migration", {
                method: "POST",
            });

            if (!response.ok) {
                throw new Error("Failed to run migration.");
            }
        }

        /**
         * Fetch reports data from the server
         * @returns {Promise<Array>} List of reports
         */
        async function fetchReports() {
            const response = await fetch("/api/reports");

            if (!response.ok) {
                throw new Error("Failed to fetch reports data.");
            }

            const data = await response.json();
            return data.reports;
        }

        /**
         * Populate the table with reports
         * @param {Array} reports List of reports
         */
        function populateReportsTable(reports) {
            reportsTableBody.innerHTML = ""; // Clear existing rows

            if (reports.length === 0) {
                const row = document.createElement("tr");
                const emptyCell = document.createElement("td");
                emptyCell.colSpan = 3;
                emptyCell.textContent = "No reports available.";
                row.appendChild(emptyCell);
                reportsTableBody.appendChild(row);
                return;
            }

            reports.forEach(report => {
                const row = document.createElement("tr");

                // Report Type
                const reportTypeCell = document.createElement("td");
                reportTypeCell.textContent = report.report_type;
                row.appendChild(reportTypeCell);

                // Time and Date
                const timeAndDateCell = document.createElement("td");
                timeAndDateCell.textContent = report.time_and_date;
                row.appendChild(timeAndDateCell);

                // Details
                const detailsCell = document.createElement("td");
                detailsCell.textContent = report.details;
                row.appendChild(detailsCell);

                reportsTableBody.appendChild(row);
            });
        }

        /**
         * Show error message
         * @param {string} message Error message to display
         */
        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.style.display = "block";
        }

        /**
         * Export the current table to PDF
         */
        function exportToPdf() {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            const table = document.querySelector("#reports-table");

            // Ensure that the table has data
            if (!table || table.rows.length === 0) {
                showError("No reports available to export.");
                return;
            }

            // Using autoTable to export the table
            doc.autoTable({
                html: '#reports-table',  // Select table by ID
                startY: 20,  // Set starting Y position for the table
                theme: 'grid',
                headStyles: { fillColor: '#1c2734' }, // Styling for header
                bodyStyles: { fillColor: '#2e3b55' }, // Styling for body
            });

            // Save the generated PDF
            doc.save("reports.pdf");
        }

    } catch (error) {
        console.error("Error:", error);
        showError("Failed to load reports. Please try again later.");
    }
});

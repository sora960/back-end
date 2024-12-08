document.addEventListener("DOMContentLoaded", async function () {
    const reportsTableBody = document.querySelector("#reports-table tbody");
    const errorDiv = document.querySelector("#error-message");

    try {
        // Run migration to ensure the latest reports are available
        await runMigration();
        console.log("Migration completed successfully.");

        // Fetch and display reports
        const reports = await fetchReports();
        populateReportsTable(reports);
    } catch (error) {
        console.error("Error:", error);
        showError("Failed to load reports. Please try again later.");
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
});

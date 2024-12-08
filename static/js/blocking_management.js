// Event listeners for fetching devices
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("fetchConnectedDevicesBtn").addEventListener("click", fetchConnectedDevices);
    document.getElementById("fetchBlockedDevicesBtn").addEventListener("click", fetchBlockedDevices);

    // Initial load of connected and blocked devices
    fetchConnectedDevices();
    fetchBlockedDevices();
});

// Show loading spinner
function showLoading() {
    const loading = document.getElementById("loading");
    if (loading) {
        loading.style.display = "block";
    }
}

// Hide loading spinner
function hideLoading() {
    const loading = document.getElementById("loading");
    if (loading) {
        loading.style.display = "none";
    }
}

// Fetch connected devices
async function fetchConnectedDevices() {
    try {
        showLoading();
        const response = await fetch('/blocking_management/connected_devices');
        if (!response.ok) throw new Error(`Error fetching connected devices: ${response.statusText}`);
        const devices = await response.json();
        populateConnectedDevices(devices);
    } catch (error) {
        console.error(error.message);
        alert("Failed to fetch connected devices. Please try again.");
    } finally {
        hideLoading();
    }
}

// Fetch blocked devices
async function fetchBlockedDevices() {
    try {
        showLoading();
        const response = await fetch('/blocking_management/blocked_devices');
        if (!response.ok) throw new Error(`Error fetching blocked devices: ${response.statusText}`);
        const devices = await response.json();
        populateBlockedDevices(devices);
    } catch (error) {
        console.error(error.message);
        alert("Failed to fetch blocked devices. Please try again.");
    } finally {
        hideLoading();
    }
}

// Populate the connected devices table
function populateConnectedDevices(devices) {
    const tableBody = document.getElementById('connectedDevicesTableBody');
    tableBody.innerHTML = '';

    const blockedMacs = new Set();
    document.querySelectorAll("#blockedDevicesTableBody tr td:first-child").forEach(td => {
        blockedMacs.add(td.innerText.trim());
    });

    const filteredDevices = devices.filter(device => !blockedMacs.has(device.mac_address));

    if (filteredDevices.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="4" class="text-center">No connected devices found.</td></tr>`;
        return;
    }

    filteredDevices.forEach(device => {
        const row = `
            <tr>
                <td>${device.mac_address}</td>
                <td>${device.ip_address}</td>
                <td>${device.hostname || 'Unknown'}</td>
                <td>
                    <button class="btn btn-danger" onclick="blockDevice('${device.mac_address}')">
                        Block
                    </button>
                </td>
            </tr>`;
        tableBody.innerHTML += row;
    });
}

// Populate the blocked devices table
function populateBlockedDevices(devices) {
    const tableBody = document.getElementById('blockedDevicesTableBody');
    tableBody.innerHTML = '';

    if (devices.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="2" class="text-center">No blocked devices found.</td></tr>`;
        return;
    }

    devices.forEach(mac => {
        const row = `
            <tr>
                <td>${mac}</td>
                <td>
                    <button class="btn btn-success" onclick="unblockDevice('${mac}')">
                        Unblock
                    </button>
                </td>
            </tr>`;
        tableBody.innerHTML += row;
    });
}

// Block a device
async function blockDevice(mac) {
    if (!confirm(`Are you sure you want to block the device with MAC: ${mac}?`)) return;

    try {
        showLoading();
        const response = await fetch('/blocking_management/block_device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mac })
        });

        if (!response.ok) throw new Error(`Error blocking device: ${response.statusText}`);
        const result = await response.json();
        alert(result.message);

        // Refresh the lists after blocking
        await fetchBlockedDevices();
        await fetchConnectedDevices();
    } catch (error) {
        console.error(error.message);
        alert("Failed to block the device. Please try again.");
    } finally {
        hideLoading();
    }
}

// Unblock a device
async function unblockDevice(mac) {
    if (!confirm(`Are you sure you want to unblock the device with MAC: ${mac}?`)) return;

    try {
        showLoading();
        const response = await fetch('/blocking_management/unblock_device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mac })
        });

        if (!response.ok) throw new Error(`Error unblocking device: ${response.statusText}`);
        const result = await response.json();
        alert(result.message);

        // Refresh the lists after unblocking
        await fetchBlockedDevices();
        await fetchConnectedDevices();
    } catch (error) {
        console.error(error.message);
        alert("Failed to unblock the device. Please try again.");
    } finally {
        hideLoading();
    }
}

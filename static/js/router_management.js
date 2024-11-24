let devices = [];
let displayedDevices = []; // To track the currently displayed devices

// Fetch Devices Function
document.getElementById('fetchDevices').addEventListener('click', async function () {
    try {
        const response = await fetch(`http://127.0.0.1:5000/devices`);
        devices = await response.json();
        displayedDevices = [...devices]; // Reset displayed devices to the full list
        populateDeviceTable(displayedDevices);
    } catch (error) {
        showResponse(`Error fetching devices: ${error.message}`, 'danger');
    }
});

// Populate Device Table
function populateDeviceTable(deviceList) {
    const deviceTableBody = document.getElementById('deviceTableBody');
    deviceTableBody.innerHTML = ''; // Clear existing rows

    if (deviceList.length === 0) {
        deviceTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No devices found</td>
            </tr>
        `;
    } else {
        deviceList.forEach((device, index) => {
            const inDhcpPool = device.in_dhcp_pool ? 'Yes' : 'No';
            const occupancy = device.occupied ? 'Occupied' : 'Available';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${device.hostname || 'Unknown'}</td>
                <td>${device.ip_address}</td>
                <td>${device.mac_address || 'N/A'}</td>
                <td>${device.lease_time ? new Date(device.lease_time * 1000).toLocaleString() : 'N/A'}</td>
                <td>${inDhcpPool}</td>
                <td>${occupancy}</td>
                <td>
                    <button class="btn btn-sm btn-primary change-ip-btn" data-index="${index}">Manage IP</button>
                </td>
            `;
            deviceTableBody.appendChild(row);
        });
    }

    // Update displayed devices
    displayedDevices = deviceList;

    // Show the device management card
    document.getElementById('deviceManagementCard').classList.remove('d-none');
}

// Sort Devices Function
function sortDevices(criteria) {
    let sortedDevices = [...displayedDevices]; // Create a copy of the currently displayed devices
    if (criteria === 'hostname') {
        sortedDevices.sort((a, b) => (a.hostname || '').localeCompare(b.hostname || ''));
    } else if (criteria === 'ip') {
        sortedDevices.sort((a, b) => a.ip_address.localeCompare(b.ip_address));
    } else if (criteria === 'occupied') {
        sortedDevices.sort((a, b) => (b.occupied ? 1 : 0) - (a.occupied ? 1 : 0));
    }
    populateDeviceTable(sortedDevices); // Repopulate the table with sorted data
}

// Filter Devices Function
function filterDevices(criteria) {
    let filteredDevices = devices;
    if (criteria === 'occupied') {
        filteredDevices = devices.filter(device => device.occupied);
    } else if (criteria === 'unoccupied') {
        filteredDevices = devices.filter(device => !device.occupied);
    }
    populateDeviceTable(filteredDevices); // Repopulate the table with filtered data
}

// Event Listener for "Manage IP" Buttons
document.getElementById('deviceTableBody').addEventListener('click', function (event) {
    if (event.target.classList.contains('change-ip-btn')) {
        const index = event.target.getAttribute('data-index');
        const selectedDevice = displayedDevices[parseInt(index, 10)]; // Use displayed devices array

        if (!selectedDevice) {
            showResponse('Device not found for the selected button.', 'danger');
            return;
        }

        // Populate modal fields
        document.getElementById('deviceDetails').value = `${selectedDevice.hostname || 'Unknown'} (IP: ${selectedDevice.ip_address})`;
        document.getElementById('new_ip').value = selectedDevice.ip_address; // Pre-fill the current IP for editing
        document.getElementById('changeIpForm').dataset.index = index; // Store index in the form

        // Show the modal
        const changeIpModal = new bootstrap.Modal(document.getElementById('changeIpModal'));
        changeIpModal.show();
    }
});

// Change IP Function
document.getElementById('changeIpForm').addEventListener('submit', async function (event) {
    event.preventDefault();

    const index = document.getElementById('changeIpForm').dataset.index;
    const selectedDevice = displayedDevices[parseInt(index, 10)];
    const new_ip = document.getElementById('new_ip').value;

    if (!selectedDevice) {
        showResponse('Failed to find the selected device.', 'danger');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/change_ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mac: selectedDevice.mac_address,
                new_ip
            })
        });

        const result = await response.json();
        showResponse(result.message, result.success ? 'success' : 'danger');

        // Hide the modal
        const changeIpModal = bootstrap.Modal.getInstance(document.getElementById('changeIpModal'));
        changeIpModal.hide();

        // Update the table if successful
        if (result.success) {
            devices = devices.map(device =>
                device.mac_address === selectedDevice.mac_address ? { ...device, ip_address: new_ip } : device
            );
            populateDeviceTable(displayedDevices); // Update the displayed table
        }
    } catch (error) {
        showResponse(`Error: ${error.message}`, 'danger');
    }
});

// Helper to Show Response Messages
function showResponse(message, type) {
    const responseEl = document.getElementById('response');
    responseEl.innerText = message;
    responseEl.className = `alert alert-${type} mt-4`;
    responseEl.classList.remove('d-none');

    // Hide after 5 seconds
    setTimeout(() => responseEl.classList.add('d-none'), 5000);
}

// Handle scanning the network
document.getElementById('scan-network-btn').addEventListener('click', function() {
    document.getElementById('loading').style.display = 'block';  // Show loading spinner

    fetch('/scan_network')
    .then(response => response.json())
    .then(data => {
        console.log("Scanned data:", data);  // Check what is received from the server
        if (data.devices && Array.isArray(data.devices)) {  // Check for 'devices' in the response
            updateTableWithScannedDevices(data.devices);  // Pass devices array for processing
        } else {
            console.error('Expected an array of devices, but got:', data);
        }
        document.getElementById('loading').style.display = 'none';  // Hide loading spinner when done
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading').style.display = 'none';  // Hide loading spinner on error
    });
});

// Update table with scanned devices
function updateTableWithScannedDevices(devices) {
    var tableBody = document.querySelector('#devices-table tbody');
    tableBody.innerHTML = '';  // Clear the table body before adding new rows

    devices.forEach(device => {
        var statusClass = device.status === 'online' ? 'status-online' : 'status-offline';
        var row = document.createElement('tr');
        row.innerHTML = `
            <td>${device.ip_address}</td>
            <td class="${statusClass}">${device.status === 'online' ? 'Online' : 'Offline'}</td>
            <td>${device.mac ? device.mac : 'N/A'}</td>
            <td>${device.device_name ? device.device_name : 'Unknown Device'}</td>
            <td>
                <button class="btn btn-primary" onclick="openAssignModal('${device.ip_address}')">Assign</button>
                <button class="btn btn-warning" onclick="blockDevice('${device.ip_address}')">Block</button>
                <button class="btn btn-danger" onclick="deleteDevice('${device.ip_address}')"><i class="fa fa-trash"></i></button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Block a device
// Function to block an IP address
function blockDevice(ip) {
    fetch('/block_ip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ip_address: ip }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("Error blocking IP:", data.error);
            alert("Failed to block IP: " + data.error);
        } else {
            console.log("IP blocked successfully:", data.message);
            alert(data.message);
            document.getElementById('scan-network-btn').click();  // Refresh the network list
        }
    })
    .catch(error => {
        console.error("Error:", error);
        alert("Error blocking IP.");
    });
}

// Add Block button to each row in the table
function updateTableWithScannedDevices(devices) {
    var tableBody = document.querySelector('#devices-table tbody');
    tableBody.innerHTML = '';  // Clear the table body before adding new rows

    devices.forEach(device => {
        var statusClass = device.status === 'online' ? 'status-online' : 'status-offline';
        var row = document.createElement('tr');
        row.innerHTML = `
            <td>${device.ip_address}</td>
            <td class="${statusClass}">${device.status === 'online' ? 'Online' : 'Offline'}</td>
            <td>${device.mac ? device.mac : 'N/A'}</td>
            <td>${device.device_name ? device.device_name : 'Unknown Device'}</td>
            <td>
                <button class="btn btn-primary" onclick="openAssignModal('${device.ip_address}')">Assign</button>
                <button class="btn btn-danger" onclick="deleteDevice('${device.ip_address}')"><i class="fa fa-trash"></i></button>
                <button class="btn btn-warning" onclick="blockDevice('${device.ip_address}')">Block</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}



// Refresh device status
function refreshDevice(ip) {
    console.log('Refreshing device status for IP:', ip);
    fetch(`/scan_device?ip_address=${ip}`)
    .then(response => response.json())
    .then(data => {
        console.log('Device refreshed:', data);
        document.getElementById('scan-network-btn').click();  // Optionally, refresh the entire table
    })
    .catch(error => console.error('Error refreshing device status:', error));
}

// Delete a device and release the IP
function deleteDevice(ip) {
    document.getElementById('loading').style.display = 'block';  // Show loading spinner while deleting
    fetch('/release_ip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ip_address: ip }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Device deleted:', data);
        document.getElementById('loading').style.display = 'none';  // Hide spinner when done
        document.getElementById('scan-network-btn').click();  // Rescan the network after deletion
    })
    .catch(error => {
        console.error('Error deleting device:', error);
        document.getElementById('loading').style.display = 'none';  // Hide spinner on error
    });
}

// Open a modal to assign IP
function openAssignModal(ip) {
    const modal = document.getElementById('assignIpModal');
    const closeBtn = document.querySelector('.close');
    const deviceIpInput = document.getElementById('device-ip');
    const deviceNameInput = document.getElementById('device-name');
    const form = document.getElementById('assign-ip-form');

    // Fetch the current device name (if available) and IP
    fetch(`/get_device_info?ip_address=${ip}`)
        .then(response => response.json())
        .then(data => {
            deviceIpInput.value = ip;
            deviceNameInput.value = data.device_name || '';  // Populate the current device name or leave blank
        })
        .catch(error => console.error('Error fetching device info:', error));

    // Show the modal
    modal.style.display = 'block';

    // Close modal when the "x" button is clicked
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    };

    // Close modal if the user clicks anywhere outside the modal
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    // Handle form submission
    form.onsubmit = function(event) {
        event.preventDefault();  // Prevent the form from submitting the traditional way

        const deviceName = document.getElementById('device-name').value;

        // Call the allocate_ip endpoint
        document.getElementById('loading').style.display = 'block';  // Show loading while assigning IP
        fetch('/allocate_ip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ip_address: ip,
                device_name: deviceName
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('IP allocated:', data);

            // Close the modal and refresh the table
            modal.style.display = 'none';
            document.getElementById('loading').style.display = 'none';  // Hide spinner when done
            document.getElementById('scan-network-btn').click();  // Rescan the network to update the table
        })
        .catch(error => {
            console.error('Error allocating IP:', error);
            document.getElementById('loading').style.display = 'none';  // Hide spinner on error
        });
    };
}

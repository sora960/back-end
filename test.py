import os

# Load the OUI database from manuf.txt
def load_manuf_file(file_path):
    manuf_dict = {}

    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding
        for line in file:
            # Ignore comments and empty lines
            if line.startswith('#') or line.strip() == '':
                continue

            # Split the line into the OUI and the manufacturer name
            parts = line.split(maxsplit=2)
            if len(parts) >= 2:
                oui = parts[0].upper()  # OUI (first 3 bytes of the MAC address) in xx:xx:xx format
                manufacturer = parts[1].strip()  # Manufacturer name
                manuf_dict[oui] = manufacturer

    return manuf_dict

# Function to get the manufacturer based on the MAC address
def get_manufacturer(mac_address, manuf_dict):
    # Extract the first 3 bytes (OUI) from the MAC address in xx:xx:xx format
    oui = mac_address[:8].upper()  # Leave in xx:xx:xx format for correct lookup

    # Debugging step: print the OUI to confirm extraction is correct
    print(f"Extracted OUI: {oui}")

    # Look up the OUI in the manufacturer dictionary
    manufacturer = manuf_dict.get(oui, "Unknown device")
    
    # Debugging step: print if the manufacturer was found
    if manufacturer == "Unknown device":
        print(f"Manufacturer not found for OUI: {oui}")
    else:
        print(f"Found Manufacturer: {manufacturer}")

    return manufacturer

# Main function to test the OUI lookup
if __name__ == "__main__":
    # Path to your manuf.txt file
    manuf_file_path = 'data/manuf.txt'  # Update the path if needed

    # Load the manufacturer data
    manuf_dict = load_manuf_file(manuf_file_path)

    # Test MAC addresses
    test_macs = [
        '1C:60:D2:64:50:10',
        'FE:4B:01:D7:8E:4C',
        'CA:21:8F:A8:33:E2',
        'E2:D1:6D:B1:97:70',
        '2C:D9:74:18:BC:BE',
        '72:68:00:A1:ED:B7',
        '26:93:93:E6:7C:8B',
        '30:07:4D:B5:9F:E4',
        '46:56:8F:40:10:14',
        'B8:F0:B9:C9:5D:65',
        '34:29:12:BF:C9:B2',
        'EE:65:B6:65:28:03'
    ]

    for mac in test_macs:
        manufacturer = get_manufacturer(mac, manuf_dict)
        print(f"MAC Address: {mac} -> Manufacturer: {manufacturer}")

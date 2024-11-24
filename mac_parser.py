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
                oui = parts[0].upper()  # OUI (first 3 bytes of the MAC address)
                manufacturer = parts[1].strip()  # Manufacturer name
                manuf_dict[oui] = manufacturer

    return manuf_dict

# Function to get the manufacturer based on the MAC address
def get_manufacturer(mac_address, manuf_dict):
    # Extract the first 3 bytes (OUI) from the MAC address
    oui = mac_address[:8].upper()  # Extracts only first 3 bytes in xx:xx:xx format
    
    # Look up the OUI in the manufacturer dictionary
    manufacturer = manuf_dict.get(oui, "Unknown device")
    
    return manufacturer

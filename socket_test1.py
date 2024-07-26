import socket
import json
import time

# Define the server address and port
server_address = ('127.0.0.1', 65432)

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)
print(f'Server listening on port {server_address[1]}')

def parse_tle_data(filename):
    satellites = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 3):
            name = lines[i].strip()
            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()

            # Simplified parsing, ideally use a proper TLE parser library
            inclination = float(line2[8:16])
            raan = float(line2[17:25])
            mean_motion = float(line2[52:63])

            # Approximate altitude using mean motion
            mu = 398600.4418  # Earth's gravitational parameter
            semi_major_axis = (mu / (mean_motion * 2 * 3.141592653589793 / 86400)**2)**(1/3)  # km
            altitude = semi_major_axis - 6371  # Earth's radius

            sat_data = {
                "name": name,
                "latitude": inclination,
                "longitude": raan,
                "altitude": altitude
            }
            satellites.append(sat_data)
    return satellites

while True:
    # Wait for a connection
    connection, client_address = sock.accept()
    try:
        print(f'Connection from: {client_address}')

        while True:
            satellite_data = parse_tle_data('starlink_satallites.txt')

            if satellite_data:
                # Print the data being sent
                print(f'Sending data: {satellite_data}')
                message = json.dumps(satellite_data)
                connection.sendall(message.encode('utf-8'))

            # Wait for 10 seconds before sending the next data
            time.sleep(10)

    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
        print(f"Client disconnected: {e}, waiting for new connection...")
        connection.close()

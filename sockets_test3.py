import socket
import json
import time
from sgp4.api import Satrec, jday
from datetime import datetime

# Define the server address and port
server_address = ('127.0.0.1', 65432)

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)
print(f'Server listening on port {server_address[1]}')

# Function to convert satellite position to Cartesian coordinates
def satellite_to_cartesian(satellite, year, month, day, hour, minute, second):
    jd, fr = jday(year, month, day, hour, minute, second)
    e, r, v = satellite.sgp4(jd, fr)
    return r

# Read TLE data from file and parse it
def parse_tle_data(filename):
    satellites = []
    with open(filename, 'r') as file:
        lines = file.readlines()

    now = datetime.utcnow()
    year, month, day = now.year, now.month, now.day
    hour, minute, second = now.hour, now.minute, now.second

    for i in range(0, len(lines), 3):
        name = lines[i].strip()
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()

        satellite = Satrec.twoline2rv(line1, line2)
        r = satellite_to_cartesian(satellite, year, month, day, hour, minute, second)

        sat_data = {
            "name": name,
            "x": r[0],
            "y": r[1],
            "z": r[2]
        }
        satellites.append(sat_data)

    return satellites

while True:
    # Wait for a connection
    connection, client_address = sock.accept()
    try:
        print(f'Connection from: {client_address}')

        satellite_data = parse_tle_data('starlink_satallites.txt')
        chunk_size = 10  # Number of satellites per chunk

        # Send data in chunks
        for i in range(0, len(satellite_data), chunk_size):
            chunk = satellite_data[i:i + chunk_size]
            message = json.dumps(chunk)
            connection.sendall(message.encode('utf-8'))
            time.sleep(1)  # Sleep for a short time to simulate streaming data

    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
        print(f"Client disconnected: {e}, waiting for new connection...")
        connection.close()
    except Exception as e:
        print(f"An error occurred: {e}")

    connection.close()







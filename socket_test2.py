import socket
import json
import time
import requests
from sgp4.api import Satrec, jday
from pyproj import Transformer
import datetime

# Define the server address and port
server_address = ('127.0.0.1', 65432)

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)
print(f'Server listening on port {server_address[1]}')

def fetch_tle_data():
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
    response = requests.get(url)
    response.raise_for_status()
    tle_lines = response.text.splitlines()
    return tle_lines

def parse_tle_data(tle_lines):
    satellites = []
    for i in range(0, len(tle_lines), 3):
        name = tle_lines[i].strip()
        line1 = tle_lines[i+1].strip()
        line2 = tle_lines[i+2].strip()
        satellites.append((name, line1, line2))
    return satellites

def get_satellite_position(name, line1, line2):
    satellite = Satrec.twoline2rv(line1, line2)
    now = datetime.datetime.utcnow()
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
    e, r, v = satellite.sgp4(jd, fr)

    if e == 0:
        transformer = Transformer.from_crs("epsg:4978", "epsg:4326")  # ECEF to WGS84
        x, y, z = r  # ECI coordinates
        lon, lat, alt = transformer.transform(x * 1000, y * 1000, z * 1000, radians=False)
        return {
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "altitude": alt
        }
    else:
        print(f"Error: {e}")
        return None

while True:
    # Wait for a connection
    connection, client_address = sock.accept()
    try:
        print(f'Connection from: {client_address}')

        while True:
            tle_lines = fetch_tle_data()
            satellites = parse_tle_data(tle_lines)
            satellite_data = None

            for sat in satellites:
                if sat[0] == "STARLINK-31785":
                    satellite_data = get_satellite_position(*sat)
                    break

            if satellite_data:
                # Print the data being sent
                print(f'Sending data: {satellite_data}')
                message = json.dumps([satellite_data])
                connection.sendall(message.encode('utf-8'))

            # Wait for 10 seconds before sending the next data
            time.sleep(10)

    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
        print(f"Client disconnected: {e}, waiting for new connection...")
        connection.close()

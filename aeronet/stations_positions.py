import csv

from aeronet.paths import SITES_POSITIONS_PATH

positions = dict()  # station: (lon, lat, elev)

with open(SITES_POSITIONS_PATH) as file:
    reader = csv.reader(file)
    next(reader)
    for station, lon, lat, elev in reader:
        lat = float(lat)
        lon = float(lon)
        elev = float(elev)
        positions[station] = (lon, lat, elev)

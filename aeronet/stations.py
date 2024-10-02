import csv

positions = dict()  # station: (lon, lat, elev)

with open("sites_positions.csv") as file:
    reader = csv.reader(file)
    next(reader)
    for station, lat, lon, elev in reader:
        lat = float(lat)
        lon = float(lon)
        elev = float(elev)
        positions[station] = (lon, lat, elev)

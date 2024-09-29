import csv

positions = dict()  # station: (lon, lat)

with open("sites_positions.csv") as file:
    reader = csv.reader(file)
    next(reader)
    for station, lat, lon in reader:
        lat = float(lat)
        lon = float(lon)
        positions[station] = (lon, lat)

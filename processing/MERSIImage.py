from datetime import datetime
from math import pi

import h5py

from .SatelliteImage import SatelliteImage

BANDS = ["5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]
BANDS_WAVELEN = {
    "5": 1380,
    "6": 1640,
    "7": 2130,
    "8": 412,
    "9": 443,
    "10": 490,
    "11": 555,
    "12": 670,
    "13": 709,
    "14": 746,
    "15": 865,
    "16": 905,
    "17": 936,
    "18": 94,
    "19": 1030,
}
E0 = {
    "1": 2017.963,
    "2": 1828.387,
    "3": 1554.807,
    "4": 952.4935,
    "5": 363.0785,
    "6": 232.4188,
    "7": 97.018,
    "8": 1700.734,
    "9": 1903.334,
    "10": 1968.184,
    "11": 1830.053,
    "12": 1504.914,
    "13": 1399.233,
    "14": 1277.788,
    "15": 955.2415,
    "16": 884.8099,
    "17": 828.4215,
    "18": 820.4936,
    "19": 680.8728,
}


class MERSIImage(SatelliteImage):
    def __init__(self, file_path: str, geo_path: str, band: str):
        self.band = band
        self.wavelength = BANDS_WAVELEN[band]
        self.file_path = file_path
        with h5py.File(file_path) as hdf, h5py.File(geo_path) as hdf_geo:
            self.latitude = hdf_geo["Geolocation"]["Latitude"][:]
            self.longitude = hdf_geo["Geolocation"]["Longitude"][:]
            self.sensor_zenith = hdf_geo["Geolocation"]["SensorZenith"][:]

            date_str = hdf.attrs["Observing Beginning Date"].decode()
            time_str = hdf.attrs["Observing Beginning Time"].decode().split(".")[0]
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            time = datetime.strptime(time_str, "%H:%M:%S").time()
            self.dt = datetime.combine(date, time)

            band_index = BANDS.index(band)
            self.counts = hdf["Data"]["EV_1KM_RefSB"][band_index][:]

            # Fix broken pixels
            self.counts[self.counts == 65535] = 0

            vis_cal = hdf["Calibration"]["VIS_Cal_Coeff"]

            Cal_0, Cal_1, Cal_2 = vis_cal[band_index]
            Slope = 1
            Intercept = 0
            dn = self.counts * Slope + Intercept
            Ref = Cal_2 * dn ** 2 + Cal_1 * dn + Cal_0

            self.radiance = Ref / 100 * E0[band] / pi

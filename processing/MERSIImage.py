import os.path
from datetime import datetime
from math import pi

import h5py
import matplotlib.pyplot as plt
import numpy as np

from paths import MERSI_L1_DIR, MERSI_L1_GEO_DIR
from .SatelliteImage import SatelliteImage

MERSI_2_BANDS = ["5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"]
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
    blackbody: np.ndarray
    space_view: np.ndarray
    voc: np.ndarray

    def __init__(self, file_path: str, geo_path: str, band: str):
        self.satellite_name = "FY-3D"
        self.band = band
        self.wavelength = BANDS_WAVELEN[band]
        self.file_path = file_path
        with h5py.File(file_path) as hdf, h5py.File(geo_path) as hdf_geo:
            self.latitude = hdf_geo["Geolocation"]["Latitude"][:]
            self.longitude = hdf_geo["Geolocation"]["Longitude"][:]
            self.sensor_zenith = hdf_geo["Geolocation"]["SensorZenith"][:]
            self.solar_zenith = hdf_geo["Geolocation"]["SolarZenith"][:]

            date_str = hdf.attrs["Observing Beginning Date"].decode()
            time_str = hdf.attrs["Observing Beginning Time"].decode().split(".")[0]
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            time = datetime.strptime(time_str, "%H:%M:%S").time()
            self.dt = datetime.combine(date, time)

            band_index = MERSI_2_BANDS.index(band)
            self.counts = hdf["Data"]["EV_1KM_RefSB"][band_index][:].astype(int)

            # Fix broken pixels
            self.counts[self.counts == 65535] = 0

            self.vis_cal = hdf["Calibration"]["VIS_Cal_Coeff"][:]
            self.blackbody = hdf["Calibration"]["BB_DN_average"][band_index + 5]
            self.space_view = hdf["Calibration"]["SV_DN_average"][band_index + 5]
            self.voc = hdf["Calibration"]["VOC_DN_average"][band_index + 5]


    def colored_image(self) -> np.ndarray:
        with h5py.File(self.file_path) as hdf:
            rsb = hdf["Data"]["EV_1KM_RefSB"]
            r = rsb[MERSI_2_BANDS.index("12")][:]
            g = rsb[MERSI_2_BANDS.index("11")][:]
            b = rsb[MERSI_2_BANDS.index("9")][:]
            r = (r // 16).astype(np.uint8)
            g = (g // 16).astype(np.uint8)
            b = (b // 16).astype(np.uint8)
            channels = [r, g, b]
            img = np.array(channels).transpose(1, 2, 0)
            return img

    @classmethod
    def from_dt(cls, dt: datetime, band: str):
        l1_fmt = "FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_1000M_MS.HDF"
        l1_geo_fmt = "FY3D_MERSI_GBAL_L1_%Y%m%d_%H%M_GEO1K_MS.HDF"
        l1_path = os.path.join(MERSI_L1_DIR, dt.strftime(l1_fmt))
        l1_geo_path = os.path.join(MERSI_L1_GEO_DIR, dt.strftime(l1_geo_fmt))
        return MERSIImage(l1_path, l1_geo_path, band)


    @property
    def radiance(self):
        band_index = MERSI_2_BANDS.index(self.band)
        Cal_0, Cal_1, Cal_2 = self.vis_cal[band_index]
        Slope = 1
        Intercept = 0
        # dn = self.counts * Slope + Intercept
        dn = (self.counts + 25) * Slope + Intercept
        # sv_column = np.repeat(self.space_view, 10).reshape((-1, 1))
        # dn = (self.counts + sv_column) * Slope + Intercept
        Ref = Cal_2 * dn ** 2 + Cal_1 * dn + Cal_0
        return Ref / 100 * E0[self.band] / pi

    @property
    def reflectance(self):
        band_index = MERSI_2_BANDS.index(self.band)
        Cal_0, Cal_1, Cal_2 = self.vis_cal[band_index]
        Slope = 1
        Intercept = 0
        dn = self.counts * Slope + Intercept
        Ref = Cal_2 * dn ** 2 + Cal_1 * dn + Cal_0
        return Ref / 100 * hdf.attrs["EarthSun Distance Ratio"] / np.cos(np.radians(self.solar_zenith / 100))

import os
from datetime import datetime

import numpy as np
from pyhdf.SD import SD

from paths import MODIS_L1B_DIR, MODIS_L1B_GEO_DIR
from .SatelliteImage import SatelliteImage

MODIS_BANDS = ["8", "9", "10", "11", "12", "13lo", "13hi", "14lo", "14hi", "15", "16", "17", "18", "19", "26"]
BANDS_WAVELEN = {
    "8": 412,
    "9": 443,
    "10": 488,
    "11": 531,
    "12": 547,
    "13lo": 667,
    "13hi": 667,
    "14lo": 678,
    "14hi": 678,
    "15": 748,
    "16": 869,
    "17": 905,
    "18": 936,
    "19": 940,
    "26": 1375,
}


class MODISImage(SatelliteImage):
    """
        00 = cloudy
        01 = uncertain clear
        10 = probably clear
        11 = confident clear
    """
    cloud_mask: np.ndarray
    scaled_integers: np.ndarray
    water_mask: np.ndarray

    def __init__(self, file_path: str, geo_path: str, band: str):
        self.satellite_name = "AQUA"
        self.file_path = file_path
        self.band = band
        self.wavelength = BANDS_WAVELEN[band]
        hdf = SD(file_path)
        geo_hdf = SD(geo_path)

        self.latitude = geo_hdf.select("Latitude")[:]
        self.longitude = geo_hdf.select("Longitude")[:]
        self.sensor_zenith = geo_hdf.select("SensorZenith")[:]
        self.solar_zenith = geo_hdf.select("SolarZenith")[:]

        RefSB = hdf.select("EV_1KM_RefSB")
        radiance_scales = RefSB.attributes()["radiance_scales"]
        radiance_offsets = RefSB.attributes()["radiance_offsets"]
        reflectance_scales = RefSB.attributes()["reflectance_scales"]
        reflectance_offsets = RefSB.attributes()["reflectance_offsets"]
        band_index = MODIS_BANDS.index(band)
        self.scaled_integers = RefSB[:][band_index]
        self.radiance = (RefSB[:][band_index].astype(float) - radiance_offsets[band_index]) * radiance_scales[
            band_index]
        self.reflectance = (RefSB[:][band_index].astype(float) - reflectance_offsets[band_index]) * reflectance_scales[
            band_index]

        water_mask_band = MODIS_BANDS.index("17")
        water_mask_radiance = (RefSB[:][water_mask_band].astype(float) - radiance_offsets[water_mask_band]) * \
                              radiance_scales[water_mask_band]
        self.water_mask = water_mask_radiance < 20.0

        self.dt = extract_datetime(hdf.attributes()["CoreMetadata.0"])

        self.create_kdtree()

    def load_cloud_mask(self, path: str):
        hdf = SD(path)
        cloud_mask = hdf.select("Cloud_Mask")[:]
        cloud_mask = cloud_mask[0]
        cloud_mask &= int("110", 2)
        cloud_mask >>= 1
        self.cloud_mask = cloud_mask

    def colored_image(self) -> np.ndarray:
        # r - B01, g - B04, b - B03
        hdf = SD(self.file_path)
        rsb250 = hdf.select("EV_250_Aggr1km_RefSB")
        rsb500 = hdf.select("EV_500_Aggr1km_RefSB")
        # r = (rsb250[0][:] / 32768) * 0.0249
        # g = (rsb500[1][:] / 32768) * 0.0188
        # b = (rsb500[0][:] / 32768) * 0.0245
        r = (rsb250[0][:] / 32768) * 3.5
        g = (rsb500[1][:] / 32768) * 3.5 / 1.38
        b = (rsb500[0][:] / 32768) * 3.5
        # r = (r // 128).astype(np.uint8)
        # g = (g // 128).astype(np.uint8)
        # b = (b // 128).astype(np.uint8)
        channels = [r, g, b]
        img = np.array(channels).transpose(1, 2, 0)
        return img

    @staticmethod
    def from_dt(dt: datetime, band: str):
        l1b_file_start = dt.strftime("MYD021KM.A%Y%j.%H%M")
        l1b_geo_file_start = dt.strftime("MYD03.A%Y%j.%H%M")
        for l1b_filename in os.listdir(MODIS_L1B_DIR):
            if l1b_filename.startswith(l1b_file_start):
                l1b_path = os.path.join(MODIS_L1B_DIR, l1b_filename)
        for l1b_geo_filename in os.listdir(MODIS_L1B_GEO_DIR):
            if l1b_geo_filename.startswith(l1b_geo_file_start):
                l1b_geo_path = os.path.join(MODIS_L1B_GEO_DIR, l1b_geo_filename)
        return MODISImage(l1b_path, l1b_geo_path, band)


def extract_date_str(meta):
    start = meta.find("RANGEBEGINNINGDATE")
    end = meta.find("RANGEBEGINNINGDATE", start + 1)
    substr = meta[start: end]
    substr = substr.split()
    date_str = substr[6].strip("\"")
    return date_str


def extract_time_str(meta):
    start = meta.find("RANGEBEGINNINGTIME")
    end = meta.find("RANGEBEGINNINGTIME", start + 1)
    substr = meta[start: end]
    substr = substr.split()
    date_str = substr[6].strip("\"")
    return date_str


def extract_datetime(meta):
    dt_str = extract_date_str(meta) + " " + extract_time_str(meta)
    return datetime.fromisoformat(dt_str)

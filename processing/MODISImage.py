import os
from datetime import datetime

import numpy as np
import pyhdf.SD
from pyhdf.SD import SD

import paths
import processing.preprocessing
from paths import MODIS_L1B_DIR, MODIS_L1B_GEO_DIR
from .SatelliteImage import SatelliteImage


MODIS_BANDS = ["8", "9", "10", "11", "12", "13lo", "13hi", "14lo", "14hi", "15", "16", "17", "18", "19", "26"]
MODIS_BANDS_WAVELEN = {
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


LAZY_MODE = True


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

    latitude: pyhdf.SD.SDS
    longitude: pyhdf.SD.SDS
    sensor_zenith: pyhdf.SD.SDS
    solar_zenith: pyhdf.SD.SDS


    def __init__(self, file_path: str, geo_path: str, band: str):
        self.satellite_name = "AQUA"
        self.file_path = file_path
        self.band = band
        self.wavelength = MODIS_BANDS_WAVELEN[band]
        self.hdf = SD(file_path)
        self.geo_hdf = SD(geo_path)

        self.latitude = self.geo_hdf.select("Latitude")
        self.longitude = self.geo_hdf.select("Longitude")
        self.sensor_zenith = self.geo_hdf.select("SensorZenith")
        self.solar_zenith = self.geo_hdf.select("SolarZenith")
        self.sensor_azimuth = self.geo_hdf.select("SensorAzimuth")
        self.solar_azimuth = self.geo_hdf.select("SolarAzimuth")

        if not LAZY_MODE:
            self.latitude = self.latitude[:]
            self.longitude = self.longitude[:]
            self.sensor_zenith = self.sensor_zenith[:]
            self.solar_zenith = self.solar_zenith[:]
            self.sensor_azimuth = self.sensor_azimuth[:]
            self.solar_azimuth = self.solar_azimuth[:]

        RefSB = self.hdf.select("EV_1KM_RefSB")
        self.band_index = MODIS_BANDS.index(band)
        self.counts = RefSB[self.band_index, :].astype(int)
        self.radiance_scales = RefSB.attributes()["radiance_scales"]
        self.radiance_offsets = RefSB.attributes()["radiance_offsets"]
        self.reflectance_scales = RefSB.attributes()["reflectance_scales"]
        self.reflectance_offsets = RefSB.attributes()["reflectance_offsets"]

        # water_mask_band = MODIS_BANDS.index("17")
        # water_mask_radiance = (RefSB[:][water_mask_band].astype(float) - radiance_offsets[water_mask_band]) * \
        #                       radiance_scales[water_mask_band]
        # self.water_mask = water_mask_radiance < 20.0

        self.dt = extract_datetime(self.hdf.attributes()["CoreMetadata.0"])

    def load_cloud_mask(self, path: str):
        hdf = SD(path)
        cloud_mask = hdf.select("Cloud_Mask")[:]
        cloud_mask = cloud_mask[0]
        cloud_mask &= int("110", 2)
        cloud_mask >>= 1
        self.cloud_mask = cloud_mask

    def colored_image(self) -> np.ndarray:
        rsb250 = self.hdf.select("EV_250_Aggr1km_RefSB")
        rsb500 = self.hdf.select("EV_500_Aggr1km_RefSB")
        r = rsb250[0][:]  # band 1
        g = rsb500[1][:]  # band 4
        b = rsb500[0][:]  # band 3

        scale250 = rsb250.attributes()["reflectance_scales"]
        offset250 = rsb250.attributes()["reflectance_offsets"]
        scale500 = rsb500.attributes()["reflectance_scales"]
        offset500 = rsb500.attributes()["reflectance_offsets"]

        r = (r.astype(float) - offset250[0]) * scale250[0]
        g = (g.astype(float) - offset500[1]) * scale500[1]
        b = (b.astype(float) - offset500[0]) * scale500[0]

        channels = [r, g, b]
        img = np.array(channels).transpose(1, 2, 0)
        img = np.minimum(img * 255 * 2, 255)
        img = img.astype(np.uint8)
        return img

    @staticmethod
    def from_dt(dt: datetime, band: str):
        l1b_file_start = dt.strftime("MYD021KM.A%Y%j.%H%M")
        l1b_geo_file_start = dt.strftime("MYD03.A%Y%j.%H%M")
        cloud_mask_file_start = dt.strftime("MYD35_L2.A%Y%j.%H%M")
        for l1b_filename in os.listdir(MODIS_L1B_DIR):
            if l1b_filename.startswith(l1b_file_start):
                l1b_path = os.path.join(MODIS_L1B_DIR, l1b_filename)
        for l1b_geo_filename in os.listdir(MODIS_L1B_GEO_DIR):
            if l1b_geo_filename.startswith(l1b_geo_file_start):
                l1b_geo_path = os.path.join(MODIS_L1B_GEO_DIR, l1b_geo_filename)
        img = MODISImage(l1b_path, l1b_geo_path, band)
        for cloud_mask_filename in os.listdir(paths.MODIS_CLOUD_MASK_DIR):
            if cloud_mask_filename.startswith(cloud_mask_file_start):
                cloud_mask_path = os.path.join(paths.MODIS_CLOUD_MASK_DIR, cloud_mask_filename)
                img.load_cloud_mask(cloud_mask_path)
        return img

    @classmethod
    def all_dts(cls) -> list[datetime]:
        dts = []
        for path in paths.MODIS_L1B_DIR.glob("*"):
            dts.append(processing.preprocessing.get_modis_file_dt(path))
        return dts

    @property
    def reflectance(self) -> np.ndarray:
        return (self.counts - self.reflectance_offsets[self.band_index]) * self.reflectance_scales[self.band_index]

    @property
    def radiance(self) -> np.ndarray:
        return (self.counts - self.radiance_offsets[self.band_index]) * self.radiance_scales[self.band_index]


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

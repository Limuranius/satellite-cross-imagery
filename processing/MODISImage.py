from datetime import datetime

import numpy as np
import satpy
from pyhdf.SD import SD

from .SatelliteImage import SatelliteImage

BANDS = ["8", "9", "10", "11", "12", "13lo", "13hi", "14lo", "14hi", "15", "16", "17", "18", "19", "26"]
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
    def __init__(self, file_path: str, band: str):
        self.file_path = file_path
        self.band = band
        self.wavelength = BANDS_WAVELEN[band]
        hdf = SD(file_path)

        self.latitude = hdf.select("Latitude")[:]
        self.longitude = hdf.select("Longitude")[:]
        self.sensor_zenith = hdf.select("SensorZenith")[:]

        RefSB = hdf.select("EV_1KM_RefSB")
        radiance_scales = RefSB.attributes()["radiance_scales"]
        radiance_offsets = RefSB.attributes()["radiance_offsets"]
        self.radiance = (RefSB[:][0].astype(float) - radiance_offsets[0]) * radiance_scales[0]

        self.dt = extract_datetime(hdf.attributes()["CoreMetadata.0"])


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

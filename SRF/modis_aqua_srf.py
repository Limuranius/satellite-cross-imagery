import os.path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from Py6S import Wavelength, PredefinedWavelengths


def get_band(band: int) -> pd.DataFrame:
    """Returns Nx2 array: wavelength and srf value"""
    filename = f"{band}.txt"
    path = os.path.join(os.path.dirname(__file__), "modis_srf", filename)
    srf_by_sensor = pd.read_csv(path)
    return srf_by_sensor[["Channel", "Wavelength", "RSR"]]


def interp_srf(band: int, step):
    srf = get_band(band)
    min_wl = srf["Wavelength"].min()
    max_wl = srf["Wavelength"].max()
    grid = np.arange(min_wl, max_wl + step * 0.0001, step)
    srf_interp = interp1d(srf["Wavelength"], srf["RSR"])
    return np.array([grid, srf_interp(grid)]).T


MODIS_6S_WV = {
    "8": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_8),
    "9": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_9),
    "10": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_10),
    "11": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_11),
    "12": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_12),
    "13lo": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_13),
    "14lo": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_14),
    "15": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_15),
    "16": Wavelength(PredefinedWavelengths.ACCURATE_MODIS_AQUA_16),
}
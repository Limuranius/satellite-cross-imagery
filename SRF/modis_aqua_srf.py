import os.path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


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


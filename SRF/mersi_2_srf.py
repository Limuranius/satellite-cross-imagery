import os.path

import numpy as np
from scipy.interpolate import interp1d


def get_band(band: int) -> np.ndarray:
    """Returns Nx2 array: wavelength and srf value"""
    filename = f"FY3D_MERSI_SRF_CH{band:>02}_Pub.txt"
    path = os.path.join(os.path.dirname(__file__), "mersi2_srf", filename)
    return np.fromfile(path, sep="   ").reshape((-1, 2))


def range_srf(band: int, start, end, step):
    grid = np.arange(start, end + step * 0.0001, step)
    values = get_band(band)
    srf = interp1d(values[:, 0], values[:, 1])
    return np.array([grid, srf(grid)]).T

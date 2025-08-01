import os.path

import numpy as np
from scipy.interpolate import interp1d
from Py6S import Wavelength


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


MERSI_6S_WV = {}
for band in range(1, 20):
    srf = get_band(int(band))
    min_wl = srf[0, 0]
    max_wl = srf[-1, 0]
    srf_grid = range_srf(int(band), min_wl, max_wl, 2.5)
    max_wl = srf_grid[-1, 0]
    wl = Wavelength(
        start_wavelength=min_wl / 1000,
        end_wavelength=max_wl / 1000,
        filter=srf_grid[:, 1],
    )
    MERSI_6S_WV[str(band)] = wl

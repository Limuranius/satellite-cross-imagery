import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from math import cos, pi, sin, acos

from aeronet.AERONETData import phase_degrees, INV_W, AERONETDataRow


def L_toa(
        aeronet_row: AERONETDataRow,
        wavelength: int,
        sat_zenith: float,
        delta_azimuth: float,
) -> float:
    Phase = np.zeros(shape=(len(phase_degrees), len(INV_W)),
                     dtype=float)  # [угол фазовой функции][длина волны]
    Knorm = np.zeros(shape=(len(phase_degrees), len(INV_W)),
                     dtype=float)  # [угол фазовой функции][длина волны]

    g443: float = aeronet_row.asymmetry_factor(443)
    g667: float = aeronet_row.asymmetry_factor(667)
    g = interp1d([441, 668], [g443, g667])

    for j, phase_deg in enumerate(phase_degrees):
        for k, wavelen in enumerate(INV_W):
            Phase[j, k] = (1 - g(k) * g(k)) / ((1 + g(k) * g(k) - 2 * g(k) * cos(phase_deg / 180 * pi)) ** 1.5)

        Knorm443 = aeronet_row.phase_function(phase_deg, 443) / Phase[j, INV_W.index(443)]
        Knorm667 = aeronet_row.phase_function(phase_deg, 667) / Phase[j, INV_W.index(667)]
        Knorm[j, :] = interp1d([441, 668], [Knorm443, Knorm667])(INV_W)

    Phase = Phase * Knorm

    AOT = aeronet_row.AOD(wavelength)
    ROT = aeronet_row.ROD(wavelength)
    SSA443 = aeronet_row.SSA(443)
    SSA667 = aeronet_row.SSA(667)
    SSA = interp1d([443, 667], [SSA443, SSA667])(INV_W)
    Lwn_FQ = aeronet_row.Lwn_FQ(wavelength)
    F0 = aeronet_row.F0(wavelength)

    d = 1 + 0.034 * cos(2 * pi * aeronet_row.day_of_year() / 365)

    solz = aeronet_row.sun_zenith

    gamma = acos(-sin(solz) * sin(senz) * cos(az) - cos(solz) * cos(senz));
    gamma_deg = gamma / pi * 180;

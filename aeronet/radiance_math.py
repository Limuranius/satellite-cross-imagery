import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from math import cos, pi

from aeronet.AERONETData import phase_degrees, INV_W

df: pd.DataFrame  # Склеенные данные OC, INV, INV_PFN

Phase = np.zeros(shape=(len(df), len(phase_degrees), len(INV_W)),
                 dtype=float)  # [номер строки][угол фазовой функции][длина волны]
Knorm = np.zeros(shape=(len(df), len(phase_degrees), len(INV_W)),
                 dtype=float)  # [номер строки][угол фазовой функции][длина волны]
Phase442: np.ndarray[float]  # [номер строки][длина волны]
Phase668: np.ndarray[float]  # [номер строки][длина волны]

for i, aeronet_row in df.iterrows():
    g442: float = aeronet_row.ASYM442
    g668: float = aeronet_row.ASYM668
    g = interp1d([441, 668], [g442, g668])

    for j, phase_deg in enumerate(phase_degrees):
        for k, wavelen in enumerate(INV_W):
            Phase[i, j, k] = (1 - g(k) * g(k)) / ((1 + g(k) * g(k) - 2 * g(k) * cos(phase_deg / 180 * pi)) ** 1.5)

        Knorm442 = Phase442[i, j] / Phase[i, j, INV_W.index(441)]
        Knorm668 = Phase668[i, j] / Phase[i, j, INV_W.index(668)]
        Knorm[i, j, :] = interp1d([441, 668], [Knorm442, Knorm668])(INV_W)

Phase = Phase * Knorm
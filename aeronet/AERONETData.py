import datetime

import pandas as pd

import aeronet
from aeronet.utils import get_closest_date_data

# Длины волн в данных с цветом океана
OC_W: list[int] = [340, 380, 400, 412, 440, 443, 490, 500, 510, 531, 532, 551, 555, 560, 620, 667, 675, 681, 709, 779,
                   865, 870, 1020]

# Длины волн в данных с фазовыми функциями
INV_W: list[int] = [443, 667, 870, 1020]

# Углы фазовой функции
phase_degrees: list[float] = [180.00, 178.29, 176.07, 173.84, 171.61, 169.37, 167.14, 164.90, 162.67, 160.43, 158.20,
                              155.96, 153.72, 151.49, 149.25, 147.02, 144.78, 142.55, 140.31, 138.07, 135.84, 133.60,
                              131.37, 129.13, 126.89, 124.66, 122.42, 120.19, 117.95, 115.71, 113.48, 111.24, 109.01,
                              106.77, 104.53, 102.30, 100.06, 97.83, 95.59, 93.35, 91.12, 90.00, 88.88, 86.65, 84.41,
                              82.17, 79.94, 77.70, 75.47, 73.23, 70.99, 68.76, 66.52, 64.29, 62.05, 59.81, 57.58, 55.34,
                              53.11, 50.87, 48.63, 46.40, 44.16, 41.93, 39.69, 37.45, 35.22, 32.98, 30.75, 28.51, 26.28,
                              24.04, 21.80, 19.57, 17.33, 15.10, 12.86, 10.63, 8.39, 6.16, 3.93, 1.71, 0.00]


class AERONETDataRow:
    OC: pd.Series
    INV: pd.Series
    INV_PFN: pd.Series

    def __init__(self, OC, INV, PFN):
        self.OC = OC
        self.INV = INV
        self.INV_PFN = PFN

    def phase_function(
            self,
            phase_degree: float,
            wavelength: int,
    ) -> float:
        fmt = "{:.6f}[{}nm]"
        return self.INV_PFN[fmt.format(phase_degree, wavelength)]


class AERONETData:
    OC: pd.DataFrame = aeronet.load_files.load_ocean_color(aeronet.paths.OCEAN_COLOR_PATH)
    INV: pd.DataFrame = aeronet.load_files.load_no_phase(aeronet.paths.AEROSOL_INVERSION_PATH)
    INV_PFN: pd.DataFrame = aeronet.load_files.load_phase(aeronet.paths.AEROSOL_INVERSION_PHASE_FUNCTION_PATH)

    def get_row(
            self,
            site: str,
            dt: datetime.datetime,
    ) -> AERONETDataRow:
        return AERONETDataRow(
            get_closest_date_data(self.OC, site, dt),
            get_closest_date_data(self.INV, site, dt),
            get_closest_date_data(self.INV_PFN, site, dt),
        )

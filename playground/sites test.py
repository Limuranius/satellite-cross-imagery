from datetime import datetime

import aeronet
from aeronet.utils import get_closest_date_data

OC = aeronet.load_files.load_ocean_color(aeronet.paths.OCEAN_COLOR_PATH)
INV = aeronet.load_files.load_no_phase(aeronet.paths.AEROSOL_INVERSION_PATH)
PFN = aeronet.load_files.load_phase(aeronet.paths.AEROSOL_INVERSION_PHASE_FUNCTION_PATH)

print(*PFN.columns, sep="\n")

dt = datetime(2024, 9, 12, 5, 30)
site = "Kemigawa_Offshore"
OC_row = get_closest_date_data(OC, site, dt)

# print(OC_row)
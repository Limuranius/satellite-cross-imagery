from pyhdf import HDF
import datetime
import os

import h5py
import paths

# Отобрать пары снимков по датам

def get_modis_dt(path: str) -> datetime.datetime:
    pass

def get_mersi_dt(path: str) -> datetime.datetime:
    with h5py.File(path) as file:
        dt_str = file.attrs["Observing Beginning Date"].decode() + " " + file.attrs["Observing Beginning Time"].decode()
        return datetime.datetime.fromisoformat(dt_str)

def get_close_pairs(max_diff = datetime.timedelta(minutes=30)) -> list[tuple[str, str]]:

    for mersi_path in os.listdir(paths.MERSI_L1_DIR):
        pass



print(get_mersi_dt(r"C:\Users\VHF\Desktop\satellite-cross-imagery\imagery\MERSI-2\L1\FY3D_MERSI_GBAL_L1_20240907_0520_1000M_MS.HDF"))
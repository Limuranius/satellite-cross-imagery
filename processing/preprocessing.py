import os
from collections import defaultdict
from datetime import datetime, timedelta

from pyhdf.SD import SD

import paths
from .MODISImage import extract_datetime


def get_modis_file_dt(file_path: str) -> datetime:
    hdf = SD(file_path)
    return extract_datetime(hdf.attributes()["CoreMetadata.0"])


def get_mersi_file_dt(file_path: str) -> datetime:
    dt_fmt = "%Y%m%d%H%M"
    filename_parts = file_path.split("_")
    return datetime.strptime(
        filename_parts[4] + filename_parts[5],
        dt_fmt
    )


def group_by_time(max_timedelta: timedelta):
    mersi_groups = defaultdict(list)
    for d in [
        paths.MERSI_L1_DIR,
        paths.MERSI_L1_GEO_DIR,
    ]:
        files = [os.path.join(d, f) for f in os.listdir(d)]
        for file_path in files:
            dt = get_mersi_file_dt(file_path)
            mersi_groups[dt].append(file_path)

    modis_groups = defaultdict(list)
    for d in [
        paths.MODIS_L1B_DIR,
        paths.MODIS_L1B_GEO_DIR,
        paths.MODIS_CLOUD_MASK_DIR,
    ]:
        files = [os.path.join(d, f) for f in os.listdir(d)]
        for file_path in files:
            dt = get_modis_file_dt(file_path)
            modis_groups[dt].append(file_path)

    l1 = mersi_groups.keys()
    l2 = modis_groups.keys()

    l1 = sorted(l1)
    l2 = sorted(l2)
    result = []
    while l1 and l2:
        t1 = l1[0]
        t2 = l2[0]
        if abs(t1 - t2) < max_timedelta:
            result.append((
                mersi_groups[l1.pop(0)],
                modis_groups[l2.pop(0)]
            ))
        else:
            if t1 < t2:
                l1.pop(0)
            else:
                l2.pop(0)
    return result

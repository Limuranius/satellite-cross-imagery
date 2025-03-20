import os
from collections import defaultdict
from datetime import datetime, timedelta

import paths


def get_modis_file_dt(file_path: str) -> datetime:
    """
    Examples:
        MYD35_L2.A2019004.2225.061.2019005170130.hdf
        MYD021KM.A2019004.2235.061.2019005165036.hdf
        MYD03.A2019004.2255.061.2019005164116.hdf
    """
    filename = os.path.basename(file_path)
    parts = filename.split(".")
    dt_str = parts[1] + parts[2]
    fmt = "A%Y%j%H%M"
    return datetime.strptime(dt_str, fmt)


def get_mersi_file_dt(file_path: str) -> datetime:
    # Example: FY3D_MERSI_GBAL_L1_20240904_1400_1000M_MS.HDF
    dt_fmt = "%Y%m%d%H%M"
    filename_parts = file_path.split("_")
    return datetime.strptime(
        filename_parts[4] + filename_parts[5],
        dt_fmt
    )


def group_by_time(max_timedelta: timedelta) -> list[tuple[tuple[str, str], tuple[str, str, str]]]:
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
    result = [pair for pair in result if len(pair[0]) == 2 and len(pair[1]) == 3]
    return result


def group_mersi_files() -> list[tuple[str, str]]:
    mersi_groups = defaultdict(list)
    for d in [
        paths.MERSI_L1_DIR,
        paths.MERSI_L1_GEO_DIR,
    ]:
        files = [os.path.join(d, f) for f in os.listdir(d)]
        for file_path in files:
            dt = get_mersi_file_dt(file_path)
            mersi_groups[dt].append(file_path)
    mersi_groups = list(mersi_groups.values())
    mersi_groups.sort(key=lambda x: get_mersi_file_dt(x[0]))
    return [file_paths for file_paths in mersi_groups if len(file_paths) == 2]


def group_modis_files() -> list[tuple[str, str]]:
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
    modis_groups = list(modis_groups.values())
    modis_groups.sort(key=lambda x: get_modis_file_dt(x[0]))
    return [file_paths for file_paths in modis_groups if len(file_paths) == 3]


def manual_group(mersi_dts: list[datetime], modis_dts: list[datetime]):
    groups = []
    for mersi_dt, modis_dt in zip(mersi_dts, modis_dts):
        print(mersi_dt, modis_dt)
        group = [[], []]
        for d in [
            paths.MERSI_L1_DIR,
            paths.MERSI_L1_GEO_DIR,
        ]:
            files = [os.path.join(d, f) for f in os.listdir(d)]
            for file_path in files:
                dt = get_mersi_file_dt(file_path)
                if dt == mersi_dt:
                    group[0].append(file_path)

        for d in [
            paths.MODIS_L1B_DIR,
            paths.MODIS_L1B_GEO_DIR,
            paths.MODIS_CLOUD_MASK_DIR,
        ]:
            files = [os.path.join(d, f) for f in os.listdir(d)]
            for file_path in files:
                dt = get_modis_file_dt(file_path)
                if dt == modis_dt:
                    group[1].append(file_path)
        assert len(group[0]) == 2 and len(group[1]) == 3
        groups.append(group)
    return groups


def filter_by_datetime(groups, start: datetime, end: datetime):
    new_groups = []
    for group in groups:
        group_dt = get_mersi_file_dt(group[0][0])
        if start <= group_dt <= end:
            new_groups.append(group)
    return new_groups


def get_mersi_dates() -> list[datetime]:
    files = [os.path.join(paths.MERSI_L1_DIR, f) for f in os.listdir(paths.MERSI_L1_DIR)]
    dates = []
    for file_path in files:
        dt = get_mersi_file_dt(file_path)
        dates.append(dt)
    return dates
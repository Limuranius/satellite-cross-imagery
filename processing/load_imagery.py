from datetime import timedelta, datetime

from .MERSIImage import MERSIImage
from .MODISImage import MODISImage
from .preprocessing import group_by_time, filter_by_datetime, group_mersi_files, get_mersi_file_dt, get_modis_file_dt, \
    group_modis_files
from typing import Generator


def iterate_close_images(
        mersi_band: str,
        modis_band: str,
        max_timedelta: timedelta = timedelta(minutes=20),
        interval: tuple[datetime, datetime] = None,
        indices: list[int] = None,
) -> Generator[tuple[MERSIImage, MODISImage], None, None]:
    groups = group_by_time(max_timedelta)
    if indices:
        groups = [groups[i] for i in range(len(groups)) if i in indices]
    if interval:
        groups = filter_by_datetime(groups, *interval)
    for (MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH) in groups:
        img_mersi = MERSIImage(
            MERSI_L1_PATH,
            MERSI_L1_GEO_PATH,
            mersi_band,
        )

        img_modis = MODISImage(
            MODIS_L1_PATH,
            MODIS_L1_GEO_PATH,
            modis_band,
        )
        img_modis.load_cloud_mask(MODIS_CLOUD_MASK_PATH)

        yield img_mersi, img_modis


def iterate_image_groups(
        groups,
        mersi_band: str,
        modis_band: str,
) -> Generator[tuple[MERSIImage, MODISImage], None, None]:
    for (MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH) in groups:
        img_mersi = MERSIImage(
            MERSI_L1_PATH,
            MERSI_L1_GEO_PATH,
            mersi_band,
        )

        img_modis = MODISImage(
            MODIS_L1_PATH,
            MODIS_L1_GEO_PATH,
            modis_band,
        )
        img_modis.load_cloud_mask(MODIS_CLOUD_MASK_PATH)

        yield img_mersi, img_modis

def iterate_mersi(
        band: str,
        interval: tuple[datetime, datetime] = None,
        dts: list[datetime] = None,
) -> Generator[MERSIImage, None, None]:
    mersi_files = group_mersi_files()
    if interval:
        filtered_files = []
        for files_pair in mersi_files:
            dt = get_mersi_file_dt(files_pair[0])
            if interval[0] <= dt <= interval[1]:
                filtered_files.append(files_pair)
        mersi_files = filtered_files
    elif dts:
        filtered_files = []
        for dt in dts:
            for files_pair in mersi_files:
                if get_mersi_file_dt(files_pair[0]) == dt:
                    filtered_files.append(files_pair)
        mersi_files = filtered_files
    for mersi_l1_path, mersi_l1_geo_path in mersi_files:
        img = MERSIImage(mersi_l1_path, mersi_l1_geo_path, band)
        yield img


def iterate_modis(
        band: str,
        interval: tuple[datetime, datetime] = None,
) -> Generator[MODISImage, None, None]:
    modis_files = group_modis_files()
    if interval:
        filtered_files = []
        for files_pair in modis_files:
            dt = get_modis_file_dt(files_pair[0])
            if interval[0] <= dt <= interval[1]:
                filtered_files.append(files_pair)
        modis_files = filtered_files
    for modis_l1_path, modis_l1_geo_path, modis_cloud_mask_path in modis_files:
        img = MODISImage(modis_l1_path, modis_l1_geo_path, band)
        img.load_cloud_mask(modis_cloud_mask_path)
        yield img

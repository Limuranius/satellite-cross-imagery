import os
import pathlib

DIR_PATH = pathlib.Path(__file__).parent


IMAGERY_DIR = DIR_PATH / "imagery"

MODIS_DIR = IMAGERY_DIR / "MODIS"
MODIS_L1B_DIR = MODIS_DIR / "L1B"
MODIS_L1B_GEO_DIR = MODIS_DIR / "L1B GEO"
MODIS_CLOUD_MASK_DIR = MODIS_DIR / "Cloud Mask"

MERSI_DIR = IMAGERY_DIR / "MERSI-2"
MERSI_L1_DIR = MERSI_DIR / "L1"
MERSI_L1_GEO_DIR = MERSI_DIR / "L1 GEO"

MATCHING_PIXELS_DIR = IMAGERY_DIR / "matching pixels"
RSTD_MAPS_DIR = IMAGERY_DIR / "relative std maps"

CALIBRATION_DIR = DIR_PATH / "calibration"
EDGE_MASKS_DIR = CALIBRATION_DIR / "edge masks"
COEFFS_DIR = CALIBRATION_DIR / "coefficients"

for dir_path in [
    MODIS_L1B_DIR,
    MODIS_L1B_GEO_DIR,
    MODIS_CLOUD_MASK_DIR,

    MERSI_L1_DIR,
    MERSI_L1_GEO_DIR,

    MATCHING_PIXELS_DIR,
    RSTD_MAPS_DIR,

    EDGE_MASKS_DIR,
]:
    os.makedirs(dir_path, exist_ok=True)

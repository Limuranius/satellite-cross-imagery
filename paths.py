import os
from os.path import join

DIR_PATH = os.path.dirname(__file__)

IMAGERY_DIR = join(DIR_PATH, "imagery")

MODIS_DIR = join(IMAGERY_DIR, "MODIS")
MODIS_L1B_DIR = join(MODIS_DIR, "L1B")
MODIS_L1B_GEO_DIR = join(MODIS_DIR, "L1B GEO")
MODIS_CLOUD_MASK_DIR = join(MODIS_DIR, "Cloud Mask")

MERSI_DIR = join(IMAGERY_DIR, "MERSI-2")
MERSI_L1_DIR = join(MERSI_DIR, "L1")
MERSI_L1_GEO_DIR = join(MERSI_DIR, "L1 GEO")

MATCHING_PIXELS_DIR = join(IMAGERY_DIR, "matching pixels")
RSTD_MAPS_DIR = join(IMAGERY_DIR, "relative std maps")

CALIBRATION_DIR = join(DIR_PATH, "calibration")
EDGE_MASKS_DIR = join(CALIBRATION_DIR, "edge masks")
COEFFS_DIR = join(CALIBRATION_DIR, "coefficients")

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

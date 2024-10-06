import os
from os.path import join

DIR_PATH = os.path.dirname(__file__)

IMAGERY_DIR = join(DIR_PATH, "imagery")
MODIS_DIR = join(IMAGERY_DIR, "MODIS")
MODIS_L1B_DIR = join(MODIS_DIR, "L1B")
MERSI_DIR = join(IMAGERY_DIR, "MERSI-2")
MERSI_L1_DIR = join(MERSI_DIR, "L1")
MERSI_L1_GEO_DIR = join(MERSI_DIR, "L1 GEO")


for dir_path in [
    MODIS_L1B_DIR,
    MERSI_L1_DIR,
    MERSI_L1_GEO_DIR,
]:
    os.makedirs(dir_path, exist_ok=True)

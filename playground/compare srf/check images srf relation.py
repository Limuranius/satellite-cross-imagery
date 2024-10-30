from datetime import timedelta

import numpy as np
import tqdm

from processing import matching
from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.matching import load_matching_pixels
from processing.preprocessing import group_by_time

MERSI_BAND = "11"
MODIS_BAND = "12"
groups = group_by_time(timedelta(minutes=30))
srf_relations = []
for (MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH) in tqdm.tqdm(groups):
    img_mersi = MERSIImage(
        MERSI_L1_PATH,
        MERSI_L1_GEO_PATH,
        MERSI_BAND,
    )

    img_modis = MODISImage(
        MODIS_L1_PATH,
        MODIS_L1_GEO_PATH,
        MODIS_BAND,
    )
    img_modis.load_cloud_mask(MODIS_CLOUD_MASK_PATH)

    pixels = load_matching_pixels(
        img_mersi, img_modis,
        # force_recalculate=True
    )

    df = matching.matching_stats(img_mersi, img_modis, pixels)

    x = df["mersi_rad"].to_numpy().astype(float)
    y = df["modis_rad"].to_numpy().astype(float)

    mask = df["modis_counts"] != 65533
    x = x[mask]
    y = y[mask]

    print((x / y).mean())
    srf_relations.append(x / y)

srf_relations = np.concatenate(srf_relations)
print(srf_relations.shape)
print(srf_relations.mean())

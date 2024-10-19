from datetime import timedelta

import matplotlib.pyplot as plt

from processing.MODISImage import MODISImage
from processing.preprocessing import group_by_time

groups = group_by_time(timedelta(minutes=30))
# (MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH) = groups[8]
# img_modis = MODISImage(
#     MODIS_L1_PATH,
#     MODIS_L1_GEO_PATH,
#     "10",
# )
# plt.hist(img_modis.scaled_integers.flatten(), bins=1000)

fig, ax = plt.subplots(nrows=3, ncols=4)

for k, ((MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH)) in enumerate(
        groups):
    img_modis = MODISImage(
        MODIS_L1_PATH,
        MODIS_L1_GEO_PATH,
        "13lo",
    )
    i = k // 4
    j = k % 4
    ax[i][j].imshow(img_modis.scaled_integers)

plt.show()

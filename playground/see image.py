from datetime import timedelta
from typing import Counter

import matplotlib.pyplot as plt

from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.preprocessing import group_by_time

# [4, 5, 7, 8, 9]

index = 8

groups = group_by_time(timedelta(minutes=30))
(MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH) = groups[index]
modis = MODISImage(
    MODIS_L1_PATH,
    MODIS_L1_GEO_PATH,
    "10"
)
mersi = MERSIImage(
    MERSI_L1_PATH,
    MERSI_L1_GEO_PATH,
    "10"
)
img = modis.scaled_integers

def format_coord(x, y):
    col = round(x)
    row = round(y)
    nrows, ncols = img.shape
    if 0 <= col < ncols and 0 <= row < nrows:
        z = img[row, col]
        return f'x={col}, y={row}, z={int(z)}'
    else:
        return f'x={col}, y={row}'


print(Counter(img[img > 2**15]))

fig, ax = plt.subplots()
ax.imshow(img, cmap="gray",
           # vmin=400,
           # vmax=600
           )
ax.format_coord = format_coord
plt.show()
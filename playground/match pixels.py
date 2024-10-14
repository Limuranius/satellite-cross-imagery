import pickle
from datetime import timedelta

import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import linregress

from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.matching import get_matching_pixels, filter_matching_pixels, visualize_matching_pixels
from processing import matching
from processing.preprocessing import group_by_time

groups = group_by_time(timedelta(minutes=30))
(MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH) = groups[0]

MODIS_BAND = "8"
MERSI_BAND = "8"

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

print(f"{img_mersi.wavelength=} {img_modis.wavelength=}")

img_modis.load_cloud_mask(MODIS_CLOUD_MASK_PATH)

# _, ax = plt.subplots(ncols=2)
# ax[0].imshow(img_modis.radiance)
# ax[1].imshow(img_modis.cloud_mask)
# plt.show()

pixels = get_matching_pixels(img_mersi, img_modis)
pixels = filter_matching_pixels(img_mersi, img_modis, pixels, max_zenith_diff=1000, max_zenith=4500)
# with open("pixels.pkl", "wb") as file:
#     pickle.dump(pixels, file)
# with open("pixels.pkl", "rb") as file:
#     pixels = pickle.load(file)

visualize_matching_pixels(
    img_mersi,
    img_modis,
    pixels
)

df = matching.matching_stats(img_mersi, img_modis, pixels)

plt.hist(df["rad_diff"], 1000)
plt.show()

# x = df["mersi_rad"].to_numpy().astype(float)
x = df["mersi_counts"].to_numpy().astype(float)
y = df["modis_rad"].to_numpy().astype(float)

# mask = (np.abs(x - y) < 90) & (np.abs(x - y) > 40) & (x > 40)
# x = x[mask]
# y = y[mask]

lin = linregress(x, y)
fig = plt.figure()
ax = fig.add_subplot()
plt.plot(x, y, "o", markersize=2)
plt.plot(x, x * lin.slope + lin.intercept, "--")
plt.xlabel("MERSI-2")
plt.ylabel("MODIS AQUA")
txt = f"""{lin.slope=:.5f}
{lin.intercept=:.5f}
{lin.rvalue**2=:.5f}
"""
plt.text(
    0,
    1,
    txt,
    horizontalalignment='left',
    verticalalignment='top',
    transform=ax.transAxes,
)
plt.show()


plt.plot(x, "o", markersize=1)
plt.plot(y, "o", markersize=1)
plt.legend(["MERSI-2", "MODIS"])

plt.show()


plt.plot(x / y, "o", markersize=1)
print((x / y).mean())
plt.show()


plt.plot(y, x / y, "o", markersize=1)
plt.xlabel("MODIS")
plt.ylabel("Relation")
plt.show()

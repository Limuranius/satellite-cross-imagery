from datetime import timedelta

from matplotlib import pyplot as plt
from scipy.stats import linregress

from processing import matching
from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.matching import visualize_matching_pixels, load_matching_pixels
from processing.preprocessing import group_by_time

# [4, 5, 7, 8, 9]
index = 8
groups = group_by_time(timedelta(minutes=30))
(MERSI_L1_PATH, MERSI_L1_GEO_PATH), (MODIS_L1_PATH, MODIS_L1_GEO_PATH, MODIS_CLOUD_MASK_PATH) = groups[index]

MODIS_BAND = "10"
MERSI_BAND = "10"

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

# plt.imshow(img_mersi.sensor_zenith / 100)
# plt.show()
# plt.imshow(img_modis.sensor_zenith / 100)
# plt.show()

print(f"{img_mersi.wavelength=} {img_modis.wavelength=}")
print("MERSI datetime:", img_mersi.dt)
print("MODIS datetime:", img_modis.dt)

pixels = load_matching_pixels(img_mersi, img_modis,
                              # force_recalculate=True
                              )

plt.plot(img_mersi.blackbody)
plt.plot(img_mersi.space_view)
plt.plot(img_mersi.voc)
plt.legend(["Blackbody", "Space View", "VOC"])
plt.show()

visualize_matching_pixels(
    img_mersi,
    img_modis,
    pixels
)

df = matching.matching_stats(img_mersi, img_modis, pixels)

x = df["mersi_rad"].to_numpy().astype(float)
# x = df["mersi_counts"].to_numpy().astype(float)
y = df["modis_rad"].to_numpy().astype(float)

# plt.hist(df["modis_rad"], 1000)
# plt.xlabel("modis_rad")
# plt.show()
#
# plt.hist(df["mersi_rad"], 1000)
# plt.xlabel("mersi_rad")
# plt.show()
#
# plt.hist(df["rad_diff"], 1000)
# plt.xlabel("rad_diff")
# plt.show()

plt.hist(x / y, 1000)
plt.xlabel("ratio")
plt.show()

# mask = (np.abs(x - y) < 90) & (np.abs(x - y) > 40) & (x > 40)
# x = x[mask]
# y = y[mask]

lin = linregress(x, y)
fig = plt.figure()
ax = fig.add_subplot()
plt.plot(x, y, "o", markersize=2)
plt.plot(x, x * lin.slope + lin.intercept, "--")
plt.title("Radiance")
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
plt.xlabel("pixel index")
plt.ylabel("radiance")
plt.legend(["MERSI-2", "MODIS"])
plt.show()

plt.plot(x / y, "o", markersize=1)
plt.xlabel("pixel index")
plt.ylabel("ratio")
print((x / y).mean())
plt.show()

plt.plot(y, x / y, "o", markersize=1)
plt.xlabel("MODIS")
plt.ylabel("ratio")
plt.show()


plt.plot(df["mersi_solz"], df["modis_solz"], "o", markersize=1)
plt.xlabel("MERSI solz")
plt.ylabel("MODIS solz")
plt.show()


plt.plot(df["mersi_solz"], df["mersi_rad"], "o", markersize=1)
plt.plot(df["modis_solz"], df["modis_rad"], "o", markersize=1)
plt.xlabel("solz")
plt.ylabel("radiance")
plt.legend(["MERSI", "MODIS"])
plt.show()
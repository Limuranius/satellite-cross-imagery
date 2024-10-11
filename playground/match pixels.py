import pickle
from matplotlib import pyplot as plt

from processing.MERSIImage import MERSIImage
from processing.MODISImage import MODISImage
from processing.matching import get_matching_pixels, filter_matching_pixels, visualize_matching_pixels
from processing import matching

img_mersi = MERSIImage(
    "/home/gleb123/satellite-cross-imagery/imagery/MERSI-2/L1/FY3D_MERSI_GBAL_L1_20240912_0350_1000M_MS.HDF",
    "/home/gleb123/satellite-cross-imagery/imagery/MERSI-2/L1 GEO/FY3D_MERSI_GBAL_L1_20240912_0350_GEO1K_MS.HDF",
    "8",
)

img_modis = MODISImage(
    "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B/MYD021KM.A2024256.0345.061.2024256152131.hdf",
    "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B GEO/MYD03.A2024256.0345.061.2024256151418.hdf",
    "8",
)

print(f"{img_mersi.wavelength=} {img_modis.wavelength=}")

img_modis.load_cloud_mask(
    "/home/gleb123/satellite-cross-imagery/imagery/MODIS/Cloud Mask/MYD35_L2.A2024256.0345.061.2024256152331.hdf")

# _, ax = plt.subplots(ncols=2)
# ax[0].imshow(img_modis.radiance)
# ax[1].imshow(img_modis.cloud_mask)
# plt.show()

# pixels = get_matching_pixels(img_mersi, img_modis)
# pixels = filter_matching_pixels(img_mersi, img_modis, pixels, max_zenith_diff=1000, max_zenith=4500)
# with open("pixels.pkl", "wb") as file:
#     pickle.dump(pixels, file)
with open("pixels.pkl", "rb") as file:
    pixels = pickle.load(file)

# visualize_matching_pixels(
#     img_mersi,
#     img_modis,
#     pixels
# )

df = matching.matching_stats(img_mersi, img_modis, pixels)

# plt.hist(df["rad_diff"], 100, range=[40, 80])

# plt.plot(df["mersi_rad"])
# plt.plot(df["modis_rad"])
plt.plot(df["mersi_rad"] / df["modis_rad"])

plt.show()

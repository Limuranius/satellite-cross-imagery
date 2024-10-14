import matplotlib.pyplot as plt

from processing import MODISImage

fig, ax = plt.subplots(nrows=4, ncols=4)

for k, band in enumerate(MODISImage.BANDS):
    i = k // 4
    j = k % 4

    img_modis = MODISImage.MODISImage(
        "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B/MYD021KM.A2024256.0345.061.2024256152131.hdf",
        "/home/gleb123/satellite-cross-imagery/imagery/MODIS/L1B GEO/MYD03.A2024256.0345.061.2024256151418.hdf",
        band,
    )

    ax[i][j].imshow(img_modis.radiance)
    ax[i][j].set_title(band)

plt.show()


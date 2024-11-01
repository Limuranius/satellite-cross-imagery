from datetime import datetime

from matplotlib import pyplot as plt

from processing.load_imagery import iterate_close_images

# 4, 5, 7, 8, 9

for i, (img_mersi, img_modis) in enumerate(iterate_close_images(
        mersi_band="8",
        modis_band="8",
)):
    plt.imshow(img_mersi.radiance)
    plt.title(str(i) + " " + str(img_mersi.dt))
    plt.show()
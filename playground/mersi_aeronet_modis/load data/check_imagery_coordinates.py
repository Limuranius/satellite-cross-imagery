import matplotlib.pyplot as plt
from tqdm import tqdm

from processing.MERSIImage import MERSIImage
from processing.preprocessing import get_mersi_dates
from stations_test import iterate_rows_timedelta_within_image

mersi_dts = get_mersi_dates()
for mersi_dt in tqdm(mersi_dts):
    image = MERSIImage.from_dt(mersi_dt, "8")
    colored = image.colored_image()
    sites = []
    for i, row in iterate_rows_timedelta_within_image(image):
        site_i, site_j = image.get_closest_pixel(row["aeronet_lon"], row["aeronet_lat"])
        sites.append((row["aeronet_lon"], row["aeronet_lat"], row["modis_t"], row["aeronet_t"], image.dt))
        radius = 4
        area_idx = [
            slice(max(0, site_i - radius), site_i + radius + 1),
            slice(max(0, site_j - radius), site_j + radius + 1),
        ]
        colored[*area_idx] = [255, 0, 0]

        plt.imshow(colored)
        txt = ""
        # for lon, lat in sites:
        #     txt += f"{lon} {lat}\n"
        for _ in sites:
            txt += str(_) + "\n"
        plt.text(
            0,
            0,
            txt,
            horizontalalignment='left',
            verticalalignment='top',
            color=(1, 0, 0)
        )
        plt.show()
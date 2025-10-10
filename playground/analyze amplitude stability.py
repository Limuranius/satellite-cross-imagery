import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from processing.MERSIImage import MERSIImage

dt = datetime.datetime(2023, 3, 30, 16, 15)
x = 400
y = 280
w = 170
h = 10

# dt = datetime.datetime(2024, 10, 1, 20, 0)
# x = 1050
# y = 890
# w = 150
# h = 10

# dt = datetime.datetime.fromisoformat("2024-06-06 19:40:00")
# x = 820
# y = 1830
# w = 150
# h = 10

# dt = datetime.datetime.fromisoformat("2024-05-25 09:55:00")
# x = 750
# y = 1160
# w = 120
# h = 10

# To excel
# with pd.ExcelWriter("amplitude_stability/area.xlsx") as writer:
#     for band in range(8, 16):
#         band = str(band)
#         img = MERSIImage.from_dt(dt, band)
#         area = img.counts[y: y + h, x: x + w]
#         pd.DataFrame(area).to_excel(writer, sheet_name=f"Band {band}", index=False, header=False)


for band in range(8, 16):
    band = str(band)
    img = MERSIImage.from_dt(dt, band)
    area = img.counts[y: y + h, x: x + w]
    mean_col = area.mean(axis=0)
    deviation = area - mean_col[None, :]

    fig, ax = plt.subplots(nrows=2, figsize=(20, 10))
    ax[0].imshow(area)
    ax[0].set_title(f"Band {band}")

    mean_abs_dev = np.abs(deviation).mean(axis=0)
    dev_norm = deviation / mean_abs_dev[None, :]

    # Flatten deviations
    dev_flat = dev_norm.T.flatten()

    ax[1].plot(dev_flat)
    ax[1].set_xlim(0, len(dev_flat))
    ax[1].set_ylabel("Нормализованное отклонение")
    plt.tight_layout()
    plt.savefig(f"amplitude_stability/{band}.png", dpi=200)
    plt.close()

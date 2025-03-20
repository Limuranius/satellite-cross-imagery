import datetime

import numpy as np
from matplotlib import pyplot as plt

from processing.MERSIImage import MERSIImage


bb = []
sv = []
voc = []


for image in MERSIImage.between_dates(
    datetime.datetime(2025, 3, 1),
    datetime.datetime(2025, 3, 10),
    "9",
):
    bb.append(image.blackbody)
    sv.append(image.space_view)
    voc.append(image.voc)

bb = np.concatenate(bb)
sv = np.concatenate(sv)
voc = np.concatenate(voc)

bb[bb == 0] = np.nan
sv[sv == 0] = np.nan
voc[voc == 0] = np.nan

min_val = min(min(bb), min(sv), min(voc))
max_val = max(max(bb), max(sv), max(voc))

plt.plot(bb)
plt.plot(sv)
plt.plot(voc)
plt.vlines(range(0, len(bb), 200), ymin=min_val, ymax=max_val)

img_count = len(bb) // 200
# numeration = list(range(-4, img_count - 4))
numeration = list(range(img_count))
for i in range(img_count):
    plt.text(i * 200 + 100, max_val, str(numeration[i]))

plt.legend(["Blackbody", "Space View", "VOC"])
plt.title(f"MERSI-2, Band 8")
plt.ylabel("DN")

plt.show()
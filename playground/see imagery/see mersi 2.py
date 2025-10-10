import datetime

import numpy as np
import tqdm

import processing.MERSIImage
from processing.MERSIImage import MERSIImage
from visuals.imagery import show_gray_with_value_adjustments
import calibration

processing.MERSIImage.LAZY_MODE = False

# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-06-06 19:35:00"), "15")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-06-06 19:35:00"), "8")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-06-06 19:35:00"), "12")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-08-03 09:55:00"), "15")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2020-10-20 04:25:00"), "15")
img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-08-03 09:55:00"), "9")

# calibration.new_correction(
#     img,
#     remove_zebra=True,
#     # remove_trace=True,
#     # correct_mean_window=True,
#     # fix_band15=True
# )

# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-06-06 19:40:00"), "15")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-05-25 09:55:00"), "12")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-10-01 20:00:00"), "12")

# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-02-09 10:10:00"), "13")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-02-06 21:15:00"), "13")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-01-30 06:35:00"), "13")

# y, x, h, w = (570, 1210, 60, 100)
# y, x, h, w = (479 - 150, 1275 - 150, 300, 300)
y, x, h, w = (570, 1210, 60, 100)
# show_gray_with_value_adjustments(img.counts)
show_gray_with_value_adjustments(img.counts[y: y + h, x: x + w])
# show_gray_with_value_adjustments(img.radiance)
# show_gray_with_value_adjustments(img.reflectance)
# show_gray_with_value_adjustments(np.log(img.counts))
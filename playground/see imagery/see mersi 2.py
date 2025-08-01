import datetime

import numpy as np

from processing.MERSIImage import MERSIImage
from visuals.imagery import show_gray_with_value_adjustments

img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-06-06 19:35:00"), "13")
#
# import calibration
# calibration.full_correct_image(img, remove_trace=True)

# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-06-06 19:40:00"), "12")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-05-25 09:55:00"), "12")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-10-01 20:00:00"), "12")

# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-02-09 10:10:00"), "13")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-02-06 21:15:00"), "13")
# img = MERSIImage.from_dt(datetime.datetime.fromisoformat("2024-01-30 06:35:00"), "13")


print("[")
show_gray_with_value_adjustments(img.counts)
print("]")
# show_gray_with_value_adjustments(np.log(img.counts))
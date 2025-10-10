from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

from processing.MERSIImage import MERSIImage
import calibration

import processing
processing.MERSIImage.LAZY_MODE = False

# 8
# MIN_VALUE = 950
# MAX_VALUE = 1200

# 12
band = "12"
MIN_VALUE = 400
MAX_VALUE = 640

# 13
# band = "13"
# MIN_VALUE = 420
# MAX_VALUE = 600

# 15
# band = "15"
# MIN_VALUE = 290
# MAX_VALUE = 400

x, y, w, h = 1225, 1360, 150, 120
# y, x, h, w = 1220, 1160, 140, 140

img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), band).counts
area = img[y: y + h, x: x + w]

fig, ax = plt.subplots()
ax.imshow(area)

fig.subplots_adjust(left=0.25)



left = Slider(
    ax=fig.add_axes([0.05, 0.2, 0.2, 0.05]),
    label=f"Left",
    valmin=0,
    valmax=15,
    valinit=0,
    valstep=1,
)
right = Slider(
    ax=fig.add_axes([0.05, 0.3, 0.2, 0.05]),
    label=f"Right",
    valmin=0,
    valmax=15,
    valinit=0,
    valstep=1,
)
coeff = Slider(
    ax=fig.add_axes([0.05, 0.4, 0.2, 0.05]),
    label=f"Coeff",
    valmin=0,
    valmax=0.15,
    valinit=0,
)

# The function to be called anytime a slider's value changes
def update(val):
    # calibration.coefficients.coeffs.COEFFS[img.band]["mean_window"]["coeffs"] = [coeff.val] * 10
    # calibration.coefficients.coeffs.COEFFS[img.band]["mean_window"]["left_window"] = left.val
    # calibration.coefficients.coeffs.COEFFS[img.band]["mean_window"]["right_window"] = right.val

    filtered_area = calibration.mean_window_correction(
        area,
        left.val,
        right.val,
        [coeff.val] * 10
    )
    ax.imshow(filtered_area, vmin=MIN_VALUE, vmax=MAX_VALUE, cmap="gray")
    fig.canvas.draw_idle()
    # print(list(coeffs))

left.on_changed(update)
right.on_changed(update)
coeff.on_changed(update)

update(1)
plt.show()

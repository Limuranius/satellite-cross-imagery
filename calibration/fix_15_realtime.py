from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

from processing.MERSIImage import MERSIImage
import calibration

import processing
processing.MERSIImage.LAZY_MODE = False

# 15
band = "15"
MIN_VALUE = 290
MAX_VALUE = 400

# x, y, w, h = 1225, 1360, 150, 120
# y, x, h, w = 1220, 1160, 140, 140
y, x, h, w = (1360, 1225, 120, 150)

img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), band)

fig, ax = plt.subplots()
ax.imshow(img.counts)
fig.subplots_adjust(left=0.25)


up = Slider(
    ax=fig.add_axes([0.05, 0.0, 0.2, 0.05]),
    label=f"up",
    valmin=0,
    valmax=15,
    valinit=15,
    valstep=1,
)
down = Slider(
    ax=fig.add_axes([0.05, 0.1, 0.2, 0.05]),
    label=f"down",
    valmin=0,
    valmax=15,
    valinit=15,
    valstep=1,
)
left = Slider(
    ax=fig.add_axes([0.05, 0.2, 0.2, 0.05]),
    label=f"Left",
    valmin=0,
    valmax=15,
    valinit=15,
    valstep=1,
)
right = Slider(
    ax=fig.add_axes([0.05, 0.3, 0.2, 0.05]),
    label=f"Right",
    valmin=0,
    valmax=15,
    valinit=15,
    valstep=1,
)
coeff0 = Slider(
    ax=fig.add_axes([0.05, 0.4, 0.2, 0.05]),
    label=f"Coeff0",
    valmin=0,
    valmax=10,
    valinit=0,
)
coeff9 = Slider(
    ax=fig.add_axes([0.05, 0.5, 0.2, 0.05]),
    label=f"Coeff9",
    valmin=0,
    valmax=10,
    valinit=0,
)

# The function to be called anytime a slider's value changes
def update(val):
    calibration.coefficients.coeffs.COEFFS[img.band]["band15_coeffs"]["coeffs"][0] = coeff0.val
    calibration.coefficients.coeffs.COEFFS[img.band]["band15_coeffs"]["coeffs"][9] = coeff9.val
    calibration.coefficients.coeffs.COEFFS[img.band]["band15_coeffs"]["left"] = left.val
    calibration.coefficients.coeffs.COEFFS[img.band]["band15_coeffs"]["right"] = right.val
    calibration.coefficients.coeffs.COEFFS[img.band]["band15_coeffs"]["up"] = up.val
    calibration.coefficients.coeffs.COEFFS[img.band]["band15_coeffs"]["down"] = down.val

    orig_counts = img.counts.copy()
    calibration.new_correction(img, fix_band15=True)
    area = img.counts[y: y+h, x:x+h]
    img.counts = orig_counts

    ax.imshow(area, vmin=MIN_VALUE, vmax=MAX_VALUE, cmap="gray")
    fig.canvas.draw_idle()

left.on_changed(update)
right.on_changed(update)
coeff0.on_changed(update)
coeff9.on_changed(update)
up.on_changed(update)
down.on_changed(update)

update(1)
plt.show()

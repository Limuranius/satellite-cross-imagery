from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

from processing.MERSIImage import MERSIImage

import apply_coeffs

# 8
MIN_VALUE = 1000
MAX_VALUE = 1100

img = MERSIImage.from_dt(datetime.fromisoformat("2024-01-30 06:35:00"), "8").counts
area = img[1650: 1800, 760: 1100]

fig, ax = plt.subplots()
ax.imshow(area)

fig.subplots_adjust(left=0.25)

# Make a vertically oriented slider to control the amplitude
coeffs_sliders = []
for sensor in range(10):
    ax_coeff = fig.add_axes([0.05, 0.1 + 0.07 * sensor, 0.2, 0.05])
    coeff_slider = Slider(
        ax=ax_coeff,
        label=f"Sensor {sensor}",
        valmin=0,
        valmax=0.1,
        valinit=0,
        # orientation="vertical"
    )
    coeffs_sliders.append(coeff_slider)


# The function to be called anytime a slider's value changes
def update(val):
    coeffs = np.zeros((10, 10))
    coeffs[0] = np.array([slider.val for slider in coeffs_sliders])

    filtered_area = apply_coeffs.apply_coeffs(area, coeffs)
    ax.imshow(filtered_area, vmin=MIN_VALUE, vmax=MAX_VALUE)
    fig.canvas.draw_idle()


for slider in coeffs_sliders:
    slider.on_changed(update)
update(1)
plt.show()

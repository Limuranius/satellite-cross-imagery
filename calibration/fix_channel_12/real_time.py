from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

from processing.MERSIImage import MERSIImage
import calibration

band = "12"
MIN_VALUE = 400
MAX_VALUE = 640

# 15
# MIN_VALUE = 290
# MAX_VALUE = 400

x, y, w, h = 1225, 1360, 150, 120
# y, x, h, w = 1220, 1160, 140, 140

img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), band)
# img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), "15").counts

fig, ax = plt.subplots()
ax.imshow(img.counts[y: y + h, x: x + w])
fig.subplots_adjust(left=0.25)

start_coeffs = calibration.coefficients.coeffs.COEFFS[band]["trace"]
# start_coeffs = np.zeros(10)


coeffs_sliders = []
for sensor in range(10):
    ax_coeff = fig.add_axes([0.05, 0.1 + 0.07 * sensor, 0.2, 0.05])
    coeff_slider = Slider(
        ax=ax_coeff,
        label=f"Sensor {sensor}",
        valmin=0,
        valmax=0.2,
        valinit=start_coeffs[sensor],
        # orientation="vertical"
    )
    coeffs_sliders.append(coeff_slider)




# The function to be called anytime a slider's value changes
def update(val):
    coeffs = np.array([slider.val for slider in coeffs_sliders])
    calibration.coefficients.coeffs.COEFFS[band]["trace"] = coeffs

    orig_counts = img.counts.copy()
    calibration.new_correction(
        img,
        correct_mean_window=True,
        remove_trace=True,
    )
    area = img.counts[y: y + h, x: x + w]
    img.counts = orig_counts

    ax.imshow(area, vmin=MIN_VALUE, vmax=MAX_VALUE, cmap="gray")
    fig.canvas.draw_idle()
    print(list(coeffs))


for slider in coeffs_sliders:
    slider.on_changed(update)
update(1)
plt.show()

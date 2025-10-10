import datetime
import pickle

import matplotlib.pyplot as plt
import numpy as np

import paths
import utils
from processing import algorithms
from processing.MERSIImage import MERSIImage
from processing.MODISChlor import MODISChlor
from visuals.graphs import InteractiveImshow
import fix_zebra


BAND = "15"
DT = datetime.datetime.fromisoformat("2024-08-03 09:55:00")
y, x, h, w = (570, 1210, 60, 100)

# vmin, vmax = 2350, 2450  # 8
# vmin, vmax = 2730, 2830  # 9
vmin, vmax = 3150, 3300  # 15

img = MERSIImage.from_dt(DT, BAND).counts
area = img[y: y + h, x: x + w]

start_coeffs = fix_zebra.apply_coeffs.load_coeffs()[int(BAND) - 5]  # shape: (10, 2) -> (sensor, slope/intercept)

sliders = []
interv = 5.0
for i in range(10):
    slope, intercept = start_coeffs[i]
    c = slope
    start = c - c * interv
    end = c + c * interv
    start, end = min(start, end), max(start, end)
    sliders.append(InteractiveImshow.SliderData(name=str(i), start=start, end=end, init=c, step=None))



class Plot(InteractiveImshow):
    sliders = sliders

    def update(self, values: dict):
        global coeffs
        coeffs = []
        for sensor in range(10):
            coeffs.append((
                values[str(sensor)],  # slope
                0,  # intercept
            ))
        coeffs = np.array(coeffs)

        new_img = fix_zebra.apply_coeffs.apply_coeffs(area, coeffs)

        self.imshow.set_data(new_img)
        self.fig.canvas.draw_idle()
        self.fig.canvas.draw_idle()


Plot(area, vmin=vmin, vmax=vmax, cmap="gray")

for sensor in range(10):
    slope, intercept = coeffs[sensor]
    print(f"{BAND},{sensor},{slope:f},{intercept:f}")

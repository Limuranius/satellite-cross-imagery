import datetime

import numpy as np

import fix_zebra
from processing.MERSIImage import MERSIImage
from visuals.graphs import InteractiveImshow

VERTICAL_AREAS = [
    dict(dt="2023-02-04 17:05:01", x=1450, y=1730, w=25),  # Слева лёд
    dict(dt="2023-02-04 17:05:01", x=1395, y=1780, w=25),  # Слева лёд
    dict(dt="2024-01-30 06:35:00", x=980, y=320, w=20),  # Слева лёд

    dict(dt="2023-03-30 16:15:01", x=400, y=410, w=25),  # Справа лёд
]

SKEWED_AREAS = [
    dict(dt="2023-01-15 23:20:00", x=780, y=640, w=40),  # Слева лёд
    dict(dt="2023-01-15 23:20:00", x=795, y=600, w=25),  # Справа лёд, с 0-5 датчики вертикально, дальше наклон

    dict(dt="2023-03-28 15:10:00", x=1110, y=1010, w=30),  # Справа лёд
    dict(dt="2023-03-28 15:10:00", x=1105, y=1020, w=30),  # Справа лёд
    dict(dt="2023-03-28 15:10:00", x=1105, y=1030, w=30),  # Справа лёд

    dict(dt="2023-03-30 16:15:01", x=420, y=340, w=40),  # Справа лёд
    dict(dt="2023-03-30 16:15:01", x=410, y=350, w=30),  # Справа лёд
    dict(dt="2023-03-30 16:15:01", x=410, y=360, w=30),  # Справа лёд
]

BAND = "8"
PAD = 50
SEPARATE_COEFFS = False

area = SKEWED_AREAS[0]
dt = datetime.datetime.fromisoformat(area["dt"])
x, y, w, h = area["x"], area["y"], area["w"], 10
x -= PAD
y -= PAD
w += PAD * 2
h += PAD * 2

vmin, vmax = {
    "8": (800, 1100),
    "9": (2730, 2830),
    "10": (800, 1100),
    "15": (3150, 3300),
}[BAND]

img = MERSIImage.from_dt(dt, BAND).counts
area = img[y: y + h, x: x + w]

INTERV = 0.5
# start_coeffs = fix_zebra.apply_norm_deviation_coeffs.load_coeffs()[int(BAND)]  # shape: (10,)
start_coeffs = np.zeros(10)  # shape: (10,)
if SEPARATE_COEFFS:
    sliders = []
    for i in range(10):
        slope = start_coeffs[i]
        c = slope
        start = c - INTERV
        end = c + INTERV
        start, end = min(start, end), max(start, end)
        sliders.append(InteractiveImshow.SliderData(name=str(i), start=start, end=end, init=c, step=None))
else:
    coeff = start_coeffs.mean()
    sliders = [
        InteractiveImshow.SliderData(
            name="common_coeff",
            start=coeff - INTERV,
            end=coeff + INTERV,
            init=coeff,
            step=None,
        )
    ]


class Plot(InteractiveImshow):
    sliders = sliders

    def update(self, values: dict):
        global coeffs
        if SEPARATE_COEFFS:
            coeffs = []
            for sensor in range(10):
                coeffs.append(values[str(sensor)])
            coeffs = np.array(coeffs)
        else:
            coeffs = np.array([values["common_coeff"]] * 10)
        new_img = fix_zebra.apply_norm_deviation_coeffs.apply_coeffs(area, coeffs)

        self.imshow.set_data(new_img)
        self.fig.canvas.draw_idle()


Plot(area, vmin=vmin, vmax=vmax, cmap="gray")

for sensor in range(10):
    slope = coeffs[sensor]
    print(f"{BAND},{sensor},{slope:f}")

from datetime import datetime

import matplotlib
import numpy as np
from matplotlib import pyplot as plt

import calibration.manually_draw_edges
from processing.MERSIImage import MERSIImage
import calculate_coeffs

matplotlib.rcParams['figure.figsize'] = (20, 10)

IMAGERY_DTS = [
    # datetime.fromisoformat("2024-01-12 13:50:00"),
    # datetime.fromisoformat("2024-01-17 15:40:00"),
    # datetime.fromisoformat("2024-01-22 17:30:00"),
    # datetime.fromisoformat("2024-01-30 06:35:00"),
    # datetime.fromisoformat("2024-02-04 08:20:00"),
    # datetime.fromisoformat("2024-02-06 21:15:00"),
    # datetime.fromisoformat("2024-02-09 10:10:00"),  # maybe 12
    # datetime.fromisoformat("2024-02-14 12:00:00"),
    # datetime.fromisoformat("2024-02-29 15:45:00"),
    # datetime.fromisoformat("2024-04-15 02:00:00"),
    # datetime.fromisoformat("2024-04-30 04:15:00"),
    # datetime.fromisoformat("2024-05-02 17:00:00"),
    # datetime.fromisoformat("2024-05-12 17:15:00"),  # maybe 12
    # datetime.fromisoformat("2024-05-15 06:10:00"),
    datetime.fromisoformat("2024-06-06 19:35:00"),  # GOAT
    datetime.fromisoformat("2024-10-01 20:00:00"),  # CHANNEL 12 GOAT
]

# Collecting all areas with edges from imagery
areas = []
for dt in IMAGERY_DTS:
    image = MERSIImage.from_dt(dt, "12").counts
    image_areas = calibration.manually_draw_edges.image_to_edge_areas(
        image,
        edge_mask=calibration.manually_draw_edges.load_edge_mask(dt, "12"),
        left_width=30,
        right_width=30,
    )
    print(len(image_areas))
    areas += image_areas

# Calculating coefficients for band 12 sensor zero
opt = calculate_coeffs.Band12Optimizer(
    areas,
    max_water_factor=2.0,
)
# opt.show()
SENSOR = 5

win_size, coeffs = opt.calculate_coeffs(SENSOR, min_win_size=5, max_win_size=11)
opt.noise_diff_relation(SENSOR, win_size, areas_indices=[1, 5, 6])
opt.noise_diff_relation(SENSOR, win_size, areas_indices=range(7, 16))


# print(opt._Band12Optimizer__error_function(coeffs, win_size, SENSOR))
coeffs[0] /= 5
coeffs[1] *= 1.7
# print(opt._Band12Optimizer__error_function(coeffs, win_size, SENSOR))

x = np.arange(2700)
y = x * coeffs[0] + x ** 2 * coeffs[1]
plt.plot(x, y, "r-")
plt.text(0, y.max(), f"y={coeffs[0]:.4f}x + {coeffs[1]:.7f}x^2\nwindow_size={win_size}")
plt.legend(["2024-06-06 19:35:00", "2024-10-01 20:00:00"])
# plt.savefig(f"/home/gleb123/Документы/20.11.24 10 канал/Коэффициенты/д{SENSOR}.png")
plt.show()

print(win_size, *coeffs)
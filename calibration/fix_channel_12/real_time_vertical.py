from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

from processing.MERSIImage import MERSIImage

# 8
# MIN_VALUE = 950
# MAX_VALUE = 1200

# 12
# MIN_VALUE = 426
# MAX_VALUE = 770

# 13
# MIN_VALUE = 370
# MAX_VALUE = 720

# 15
MIN_VALUE = 290
MAX_VALUE = 400

# x, y, w, h = 1225, 1360, 150, 120
y, x, h, w = 1220, 1160, 140, 140

# img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), "8").counts
# img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), "12").counts
# img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), "13").counts
img = MERSIImage.from_dt(datetime.fromisoformat("2024-06-06 19:35:00"), "15").counts
area = img[y: y + h, x: x + w]

fig, ax = plt.subplots()
ax.imshow(area)

fig.subplots_adjust(left=0.25)


def gkern(l=5, sig=1.):
    """
    creates gaussian kernel with side length `l` and a sigma of `sig`
    """
    ax = np.linspace(-(l - 1) / 2., (l - 1) / 2., l)
    gauss = np.exp(-0.5 * np.square(ax) / np.square(sig))
    kernel = gauss
    return kernel / np.sum(kernel)


def predict_horizontal_noise_full(counts, horizontal_coeffs, horizontal_radius=10):
    h, w = counts.shape
    k = horizontal_radius * 2 + 1  # kernel size
    kernel = gkern(k, sig=5)  # [k] normal distribution kernel

    size = counts.dtype.itemsize

    counts_pad = np.pad(counts, ((0, 0), (horizontal_radius, horizontal_radius)))
    counts_windows = np.lib.stride_tricks.as_strided(  # Свёртка, применяем страйды
        counts_pad,
        shape=(
            h,
            w,  # изначальная ширина без паддинга
            k,  # ширина окна
        ),
        strides=(
            size * counts_pad.shape[1],
            size,
            size,
        )
    )

    diff = counts_windows - counts[..., None]  # [h*w*k] Разница с пикселями внутри одного окна
    diff[diff < 0] = 0
    diff = diff * kernel[None, None]  # weighted difference
    # mean_diff = diff.mean(axis=2)
    mean_diff = diff.sum(axis=2)
    scans_count = h // 10
    pred_noise = mean_diff * np.tile(horizontal_coeffs, scans_count)[:, None]  # [h*w]
    return pred_noise

# def predict_vertical_noise_full(counts, vertical_coeffs):
#     h, w = counts.shape
#     pred_noise = np.zeros_like(counts)
#
#     for scan_number in range(h // 10):
#         scan_counts = counts[scan_number * 10: (scan_number + 1) * 10]
#         scan_diff = scan_counts[None, :, :] - scan_counts[:, None, :]
#         scan_diff[scan_diff < 0] = 0  # [10, 10, w]
#         each_sensor_noise = scan_diff * vertical_coeffs[:, :, None]
#         pred_noise[scan_number * 10: (scan_number + 1) * 10] = each_sensor_noise.max(axis=1)
#     return pred_noise


def predict_vertical_noise_full(counts, vertical_coeffs, window_left=1, window_right=1):
    h, w = counts.shape
    pred_noise = np.zeros_like(counts)

    for scan_number in range(h // 10):
        scan_counts = counts[scan_number * 10: (scan_number + 1) * 10]
        for sensor in range(10):
            for j in range(w):
                window = scan_counts[:, max(0, j - window_left): min(w-1, j + window_right)]
                diff = window - scan_counts[sensor, j]
                noise = vertical_coeffs[sensor][:, None] * diff
                max_noise = noise.max()
                pred_noise[scan_number * 10 + sensor, j] = max_noise
    return pred_noise



# horiz_coeffs = [0.03904511, 0.05486233, 0.0794669, 0.11110135, 0.13687756, 0.15210896
#     , 0.13101933, 0.09352665, 0.05896309, 0.0413884]
horiz_coeffs = np.zeros(10)

coeffs_sliders = []
for sensor in range(10):
    ax_coeff = fig.add_axes([0.05, 0.1 + 0.07 * sensor, 0.2, 0.05])
    coeff_slider = Slider(
        ax=ax_coeff,
        label=f"Sensor {sensor}",
        valmin=0,
        valmax=0.04,
        valinit=0,
        # orientation="vertical"
    )
    coeffs_sliders.append(coeff_slider)




# The function to be called anytime a slider's value changes
def update(val):
    coeffs = np.array([slider.val for slider in coeffs_sliders])
    vertical_coeffs = np.repeat(coeffs[:, None], 10, axis=1)

    noise = predict_horizontal_noise_full(area, horiz_coeffs)
    noise += predict_vertical_noise_full(area, vertical_coeffs)
    filtered_area = area - noise
    ax.imshow(filtered_area, vmin=MIN_VALUE, vmax=MAX_VALUE)
    fig.canvas.draw_idle()
    print(list(coeffs))


for slider in coeffs_sliders:
    slider.on_changed(update)
update(1)
plt.show()

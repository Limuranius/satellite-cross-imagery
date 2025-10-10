import numpy as np

from processing.MERSIImage import MERSIImage
from . import (
    manually_draw_edges,
    fix_channel_8,
    fix_channel_12,
    fix_zebra,
    fix_coefficients,
    fix_intercept,
)
from .coefficients.coeffs import COEFFS


def full_correct_image(
        image: MERSIImage,
        remove_zebra: bool = False,
        remove_neighbor_influence: bool = False,
        remove_trace: bool = False,
        fix_coeffs: bool = False,
) -> None:
    if remove_zebra:
        fix_zebra.apply_coeffs.correct_mersi_image(image)
    if fix_coeffs:
        fix_coefficients.fix_coeffs(image)
    match image.band:
        case "8":
            if remove_neighbor_influence:
                fix_channel_8.apply_coeffs.correct_mersi_image(image)
        case "12":
            if remove_trace:
                fix_channel_12.apply_coeffs.correct_mersi_image(image)


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


def area_vertical_mean(counts, w_left, w_right):
    h, w = counts.shape
    size = counts.dtype.itemsize
    counts_pad = np.pad(counts, ((0, 0), (w_left, w_right)))
    counts_windows = np.lib.stride_tricks.as_strided(  # Свёртка, применяем страйды
        counts_pad,
        shape=(
            10,  # 10 датчиков
            w,  # изначальная ширина без паддинга
            w_left + w_right + 1,  # ширина окна
        ),
        strides=(
            size * counts_pad.shape[1],
            size,
            size,
        )
    )
    return counts_windows.mean(axis=(0, 2))

def mean_window_correction(counts, left_w, right_w, coeffs):
    new_counts = counts.copy()
    for scan in range(counts.shape[0] // 10):
        mean = area_vertical_mean(
            counts[scan * 10: (scan + 1) * 10],
            left_w,
            right_w,
        )
        for sensor in range(10):
            noise = (mean - counts[scan * 10 + sensor]) * coeffs[sensor]
            noise[noise < 0] = 0
            new_counts[scan * 10 + sensor] -= noise.astype(int)
    return new_counts

def new_correction(
        image: MERSIImage,
        remove_zebra: bool = False,
        remove_zebra_normalized_dev: bool = False,
        remove_neighbor_influence: bool = False,
        remove_trace: bool = False,
        correct_mean_window: bool = False,
        fix_band15: bool = False,
):
    if remove_zebra and remove_zebra_normalized_dev:
        raise Exception("Can't combine zebra correction")
    if remove_zebra:
        fix_zebra.apply_coeffs.correct_mersi_image(image)
    if remove_zebra_normalized_dev:
        fix_zebra.apply_norm_deviation_coeffs.correct_mersi_image(image)
    if remove_neighbor_influence:
        noise = predict_vertical_noise_full(
            image.counts,
            vertical_coeffs=COEFFS[image.band]["neighbor_influence"],
            window_left=COEFFS[image.band]["left_window"],
            window_right=COEFFS[image.band]["right_window"],
        )
        image.counts -= noise.astype(int)
    if remove_trace:
        noise = predict_horizontal_noise_full(
            image.counts,
            horizontal_coeffs=COEFFS[image.band]["trace"],
        )
        image.counts -= noise.astype(int)
    if correct_mean_window:
        image.counts = mean_window_correction(
            image.counts,
            COEFFS[image.band]["mean_window"]["left_window"],
            COEFFS[image.band]["mean_window"]["right_window"],
            coeffs=COEFFS[image.band]["mean_window"]["coeffs"],
        )
    if fix_band15 and image.band == "15":
        # Нечётные сканы, первый и последний датчики
        def vertical_mean(counts, w_left, w_right, h_up, h_down):
            h, w = counts.shape
            size = counts.dtype.itemsize
            counts_pad = np.pad(counts, ((h_up, h_down), (w_left, w_right)))
            counts_windows = np.lib.stride_tricks.as_strided(  # Свёртка, применяем страйды
                counts_pad,
                shape=(
                    h,  # 10 датчиков
                    w,  # изначальная ширина без паддинга
                    h_up + h_down + 1,  # высота окна
                    w_left + w_right + 1,  # ширина окна
                ),
                strides=(
                    size * counts_pad.shape[1],
                    size,
                    size * counts_pad.shape[1],
                    size,
                )
            )
            return counts_windows.mean(axis=(-1, -2))
        m = vertical_mean(
            image.counts,
            COEFFS[image.band]["band15_coeffs"]["left"],
            COEFFS[image.band]["band15_coeffs"]["right"],
            COEFFS[image.band]["band15_coeffs"]["up"],
            COEFFS[image.band]["band15_coeffs"]["down"],
        )
        noise = m - image.counts
        noise[noise < 0] = 0
        noise = np.log(noise + 1)

        for scan in range(200):
            if scan % 2 == 0:
                continue
            sl = slice(scan * 10, (scan + 1) * 10)
            image.counts[sl] -= (noise[sl] * COEFFS[image.band]["band15_coeffs"]["coeffs"][:, None]).astype(int)

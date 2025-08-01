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


def new_correction(
        image: MERSIImage,
        remove_zebra: bool = False,
        remove_neighbor_influence: bool = False,
        remove_trace: bool = False,
):
    if remove_zebra:
        fix_zebra.apply_coeffs.correct_mersi_image(image)
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

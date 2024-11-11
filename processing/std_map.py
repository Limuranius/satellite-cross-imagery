import os

import numpy as np
from scipy.signal import convolve2d
from tqdm import tqdm

import paths
from processing.SatelliteImage import SatelliteImage


def get_rstd_map_path(img: SatelliteImage, kernel_size: int):
    date_str = img.dt.strftime("%Y%m%d%H%M")
    file_name = f"{img.satellite_name} {date_str} band{img.band} kernel{kernel_size}.npy"
    return os.path.join(
        paths.RSTD_MAPS_DIR,
        file_name
    )


def mean_convolve(arr: np.ndarray, kernel_size: int):
    n = kernel_size * kernel_size
    kernel = np.ones(shape=(kernel_size, kernel_size))
    conv_res = convolve2d(arr, kernel, mode="same")
    return conv_res / n


def std_convolve(arr: np.ndarray, kernel_size: int):
    n = kernel_size * kernel_size
    mean = mean_convolve(arr, kernel_size)

    # Subtracting mean from each window
    win_subtracts = []
    for dx in range(-(kernel_size // 2), kernel_size // 2 + 1):
        for dy in range(-(kernel_size // 2), kernel_size // 2 + 1):
            shifted_arr = np.roll(arr, (dy, dx), (0, 1))
            win_subtracts.append(shifted_arr - mean)

    win_subtracts = np.array(win_subtracts) ** 2
    win_diff_sq_sum = win_subtracts.sum(axis=0)
    std = np.sqrt(win_diff_sq_sum / n)
    return std


def rstd_convolve(arr: np.ndarray, kernel_size: int):
    mean = mean_convolve(arr, kernel_size)
    std = std_convolve(arr, kernel_size)
    return std / mean


def load_rstd_map(img: SatelliteImage, kernel_size: int) -> np.ndarray:
    file_path = get_rstd_map_path(img, kernel_size)
    if os.path.exists(file_path):
        return np.load(file_path)
    else:
        print("Calculating rstd array... ", end="")
        rstd_map = rstd_convolve(img.radiance, kernel_size)
        print("Done!")
        np.save(file_path, rstd_map)
        return rstd_map

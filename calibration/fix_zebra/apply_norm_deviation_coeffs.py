import os

import numpy as np
import tqdm
import paths
from processing.MERSIImage import MERSIImage
import pickle


def load_coeffs() -> np.ndarray:
    """
    dict[int, float[10]]
    """
    path = os.path.join(paths.COEFFS_DIR, "zebra_norm_deviation_coeffs.pickle")
    with open(path, "rb") as file:
        coeffs = pickle.load(file)
    return coeffs
    # array = []
    # for band_coeffs in coeffs.values():
    #     array.append(np.array([
    #         band_coeffs["side1"],
    #         band_coeffs["side2"],
    #     ]).T)
    # return np.array(array)


def apply_coeffs(image: np.ndarray, coeffs: np.ndarray):
    """
    image - int[2000, 2048]
    coeffs - float[10]
    """
    h = image.shape[0]
    new_image = image.copy()

    for i in range(0, h, 10):
        scan = image[i: i + 10]
        mean_col = scan.mean(axis=0)
        deviation = scan - mean_col[None, :]
        abs_dev = np.abs(deviation)
        mean_abs_dev = abs_dev.mean(axis=0)
        zebra_noise = mean_abs_dev[None, :] * coeffs[:, None]
        new_image[i: i + 10] -= zebra_noise.astype("int16")
    return new_image


def correct_mersi_image(image: MERSIImage) -> None:
    coeffs = load_coeffs()
    band_coeffs = coeffs[int(image.band)]
    image.counts = apply_coeffs(image.counts, band_coeffs)


